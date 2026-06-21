"""Modal deploy entry for Scrapling.

Web page -> text/markdown using Scrapling's StealthyFetcher (a stealth,
anti-detection browser running on CPU). Solves Cloudflare challenges and
mimics a real browser fingerprint, so it succeeds on pages that a plain
HTTP fetch cannot reach.

Scrapling (BSD 3-Clause, (c) Karim Shoair / D4Vinci):
https://github.com/D4Vinci/Scrapling

Deploy:
  modal deploy deploy.py
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import modal
from tongflow import deploy
from tongflow.models.link import LinkInput, LinkOutput
from tongflow.node_slots import NodeSlots
from tongflow.slots import node_slot

# Pin Scrapling so the baked-in browser matches the library. Browser binaries
# are installed into the image at build time (`scrapling install`), so there is
# no per-request download step.
SCRAPLING_VERSION = "0.4.9"

# Plugin-internal fetch tuning. These are not ABI fields: only this plugin
# needs them, so they live here as constants (see CLAUDE.md "ABI gaps").
SOLVE_CLOUDFLARE = True  # auto-solve Cloudflare Turnstile/Interstitial
NETWORK_IDLE = True  # wait until the page stops making network requests
DISABLE_RESOURCES = True  # drop fonts/images/media for a speed boost
BLOCK_ADS = True  # block ~3,500 known ad/tracking domains
FETCH_TIMEOUT_MS = 60_000  # per-operation page timeout

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        f"scrapling[fetchers]=={SCRAPLING_VERSION}",
        "markdownify>=1.2.0",
        "tongflow==0.1.0",
    )
    # Bake the stealth browser + its system deps into the image layer.
    # `scrapling` is a pip console script (PATH), not a runnable module.
    .run_commands("scrapling install")
)

app = modal.App(Path(__file__).resolve().parent.name, image=image)
secrets = modal.Secret.from_dict({})

with image.imports():
    from markdownify import markdownify as html_to_markdown
    from scrapling.fetchers import StealthyFetcher


def _scrape_to_text(url: str) -> dict[str, Any]:
    """Fetch `url` with the stealth browser and return clean markdown text."""
    page = StealthyFetcher.fetch(
        url,
        headless=True,
        solve_cloudflare=SOLVE_CLOUDFLARE,
        network_idle=NETWORK_IDLE,
        disable_resources=DISABLE_RESOURCES,
        block_ads=BLOCK_ADS,
        timeout=FETCH_TIMEOUT_MS,
    )

    status = int(getattr(page, "status", 0) or 0)
    if status and status >= 400:
        return {"success": False, "error": f"fetch failed: HTTP {status}"}

    # Prefer structured markdown (keeps headings/links); fall back to flat text.
    markdown = ""
    try:
        markdown = html_to_markdown(str(page.html_content), heading_style="ATX").strip()
    except Exception as e:  # markdownify is best-effort; plain text still works
        logger.warning(f"markdownify failed, falling back to plain text: {e}")
    if not markdown:
        markdown = str(page.get_all_text(strip=True))

    if not markdown:
        return {"success": False, "error": "page returned no extractable text"}

    return {"success": True, "url": url, "markdown": markdown}


def _scrape_core(url: str | None) -> dict[str, Any]:
    if not url:
        return {"success": False, "error": "missing url in prompt"}
    logger.info(f"scrape start: {url}")
    try:
        result = _scrape_to_text(url)
    except Exception as e:
        logger.error(f"scrape failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
    if result.get("success"):
        logger.info(f"scrape ok: {url} len={len(result.get('markdown') or '')}")
    else:
        logger.error(f"scrape error: {url} -> {result.get('error')}")
    return result


@deploy
@app.cls(cpu=2.0, memory=4096, timeout=600, secrets=[secrets], scaledown_window=120)
class Inference:
    @modal.method()
    @node_slot(NodeSlots.LINK)
    def link(self, input: LinkInput) -> LinkOutput:
        result = _scrape_core(input.url)
        if not result.get("success"):
            return LinkOutput(
                success=False,
                error=str(result.get("error") or "scrape failed"),
            )
        return LinkOutput(
            success=True,
            mainText=str(result.get("markdown") or ""),
        )
