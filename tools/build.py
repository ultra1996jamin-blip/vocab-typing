#!/usr/bin/env python3
"""Optional: build ONE offline file (words + all audio embedded) at dist/vocab-typing-offline.html.

The normal app (index.html) needs no build: it reads data/words.json and data/audio/ when it opens.
Use this only when you want a single file you can double-click without a server, or to hand to someone.

    python tools/build.py
"""
import base64, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
words = json.loads((ROOT / "data/words.json").read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "data/audio/manifest.json").read_text(encoding="utf-8"))
voices = []
for v in manifest["voices"]:
    ws = {k: {"d": r["d"], "b64": base64.b64encode((ROOT / r["f"]).read_bytes()).decode()} for k, r in v["words"].items()}
    voices.append({"id": v["id"], "label": v["label"], "words": ws})

html = (ROOT / "index.html").read_text(encoding="utf-8")
marker = '<script>\n/* ---- data loader'
assert marker in html, "loader marker missing in index.html"
inline = "<script>window.APP_INLINE = " + json.dumps({"words": words, "voices": voices}, ensure_ascii=False, separators=(",", ":")) + ";</script>\n"
out = html.replace(marker, inline + marker, 1)
dst = ROOT / "dist/vocab-typing-offline.html"
dst.parent.mkdir(exist_ok=True)
dst.write_text(out, encoding="utf-8")
print(f"{dst.relative_to(ROOT)} {len(out.encode('utf-8')):,} bytes · {len(words)} words · voices: {[v['id'] for v in voices]}")
