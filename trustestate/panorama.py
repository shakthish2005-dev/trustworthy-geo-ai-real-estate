from __future__ import annotations

import base64
import json
from pathlib import Path


def panorama_html(image_bytes: bytes, title: str = "Property panorama") -> str:
    encoded = base64.b64encode(image_bytes).decode("ascii")
    safe_title = json.dumps(title)
    return f"""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pannellum@2.5.6/build/pannellum.css" />
    <script src="https://cdn.jsdelivr.net/npm/pannellum@2.5.6/build/pannellum.js"></script>
    <div id="panorama" style="width:100%;height:540px;border-radius:16px;overflow:hidden;background:#071827"></div>
    <script>
      pannellum.viewer('panorama', {{
        type: 'equirectangular',
        panorama: 'data:image/png;base64,{encoded}',
        autoLoad: true,
        compass: true,
        showFullscreenCtrl: true,
        showZoomCtrl: true,
        title: {safe_title},
        hfov: 105
      }});
    </script>
    """


def load_panorama(path: Path) -> bytes:
    return path.read_bytes()
