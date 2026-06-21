# tongflow-modal-scrapling

Official [TongFlow](https://github.com/tong-io/tongflow) plugin. URL/link-to-text extraction with **[Scrapling](https://github.com/D4Vinci/Scrapling)**, running on [Modal](https://modal.com) CPU. Fetches a page with a stealth, anti-detection browser and turns its content into clean markdown text.

Unlike a plain HTTP fetch, Scrapling's `StealthyFetcher` runs a real browser with a spoofed fingerprint and can auto-solve Cloudflare challenges, so it succeeds on JavaScript-heavy and bot-protected pages — at the cost of a heavier image and slower cold start. The browser is CPU-only (no GPU required).

## Capabilities

- **Link → text** (`link`) — fetch a web page and convert its content to markdown text.

## Credentials

Add in TongFlow **Settings** (gear icon, top-right):

| Key | Required | Notes |
| --- | --- | --- |
| `MODAL_TOKEN_ID` | ✅ | Create at [modal.com/settings/tokens](https://modal.com/settings/tokens). |
| `MODAL_TOKEN_SECRET` | ✅ | Paired with `MODAL_TOKEN_ID`. |

On first use the plugin deploys to your Modal account automatically and caches the build (browser binaries are baked into the image). No Hugging Face token required.

## Credits

Powered by [Scrapling](https://github.com/D4Vinci/Scrapling) by Karim Shoair (D4Vinci), licensed under the [BSD 3-Clause License](https://github.com/D4Vinci/Scrapling/blob/main/LICENSE).
