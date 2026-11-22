#!/usr/bin/env python3
"""Build index.html: inject the word list and the voice packs into src/app.html.

Run from the repo root:  python tools/build.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOICE_ORDER = ["heart", "michael", "supertonic"]  # first one is the default voice

words = json.loads((ROOT / "data/words.json").read_text(encoding="utf-8"))
voices = []
for vid in VOICE_ORDER:
    f = ROOT / "data/voices" / f"{vid}.json"
    if f.exists():
        voices.append(json.loads(f.read_text(encoding="utf-8")))

src = (ROOT / "src/app.html").read_text(encoding="utf-8")
assert "/*WORDS*/[]" in src and '/*AUDIO*/{"voices":[]}' in src, "placeholders missing in src/app.html"
out = src.replace("/*WORDS*/[]", json.dumps(words, ensure_ascii=False, separators=(",", ":")))
out = out.replace('/*AUDIO*/{"voices":[]}', json.dumps({"voices": voices}, ensure_ascii=False, separators=(",", ":")))
(ROOT / "index.html").write_text(out, encoding="utf-8")

missing = [w["en"] for w in words for v in voices if w["en"].lower() not in v["words"]]
print(f"index.html {len(out.encode('utf-8')):,} bytes · {len(words)} words · voices: {[v['id'] for v in voices]}")
if missing:
    print("WARNING: words without built-in audio (browser TTS will be used):", sorted(set(missing)))
