"""Modal download entry for Scrapling.

Run:
  modal run download.py::download
"""

from __future__ import annotations

import modal

app = modal.App("scrapling-download")


@app.local_entrypoint()
def download() -> None:
    # The stealth browser is installed into the image layer at build time
    # (`scrapling install` in deploy.py), so there is nothing to download here.
    print("No download step required for scrapling.")
