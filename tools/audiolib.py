"""Shared helpers for the audio files: data/audio/<voice>/<slug>.mp3 + data/audio/manifest.json

manifest: {"voices": [{"id", "label", "words": {word_lowercase: {"d": seconds, "f": "data/audio/<voice>/<slug>.mp3"}}}]}
The first voice in the list is the app's default.
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIO = ROOT / "data/audio"
MANIFEST = AUDIO / "manifest.json"
VOICE_ORDER = ["heart", "michael", "supertonic"]


def slug(word):
    return re.sub(r"[^a-z0-9]+", "-", word.lower()).strip("-") or "word"


def load():
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"voices": []}


def save(m):
    rank = lambda v: (VOICE_ORDER.index(v["id"]) if v["id"] in VOICE_ORDER else len(VOICE_ORDER), v["id"])
    m["voices"].sort(key=rank)
    AUDIO.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")


def voice(m, vid, label=None):
    for v in m["voices"]:
        if v["id"] == vid:
            if label:
                v["label"] = label
            return v
    v = {"id": vid, "label": label or vid, "words": {}}
    m["voices"].append(v)
    return v


def mp3_path(vid, word):
    return AUDIO / vid / f"{slug(word)}.mp3"
