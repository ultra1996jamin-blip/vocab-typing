#!/usr/bin/env python3
"""Build index.html: inject the word list and the voice packs into src/app.html.

Run from the repo root:  python tools/build.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOICE_ORDER = ["heart", "michael", "supertonic"]  # first one is the default voice

words = json.loads((ROOT / "data/words.json").read_text(encoding="utf-8"))
packs = {f.stem: f for f in (ROOT / "data/voices").glob("*.json")}
order = [v for v in VOICE_ORDER if v in packs] + sorted(v for v in packs if v not in VOICE_ORDER)
voices = [json.loads(packs[v].read_text(encoding="utf-8")) for v in order]

src = (ROOT / "src/app.html").read_text(encoding="utf-8")
assert "/*WORDS*/[]" in src and '/*AUDIO*/{"voices":[]}' in src, "placeholders missing in src/app.html"
out = src.replace("/*WORDS*/[]", json.dumps(words, ensure_ascii=False, separators=(",", ":")))
out = out.replace('/*AUDIO*/{"voices":[]}', json.dumps({"voices": voices}, ensure_ascii=False, separators=(",", ":")))
(ROOT / "index.html").write_text(out, encoding="utf-8")

print(f"index.html {len(out.encode('utf-8')):,} bytes · {len(words)} words · voices: {[v['id'] for v in voices]}")
for v in voices:
    miss = [w["en"] for w in words if w["en"].lower() not in v["words"]]
    if miss:
        print(f"note: voice '{v['id']}' lacks {len(miss)} words; the app borrows another built-in voice for them")
nowhere = [w["en"] for w in words if not any(w["en"].lower() in v["words"] for v in voices)]
if nowhere:
    print("WARNING: no built-in audio at all (browser TTS will be used):", nowhere)
