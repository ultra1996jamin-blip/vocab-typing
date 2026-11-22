#!/usr/bin/env python3
"""Generate trimmed US-English clips with Kokoro v1.0 (sherpa-onnx), one JSON voice pack per speaker.

usage: python tools/gen_kokoro.py data/words.json data/voices/heart.json 3 heart "여자 · Heart (Kokoro, 추천)"
       python tools/gen_kokoro.py data/words.json data/voices/michael.json 16 michael "남자 · Michael (Kokoro)"
out.json = {"id":..., "label":..., "words": {word: {"d": sec, "b64": mp3}}}

needs: pip install sherpa-onnx numpy soundfile, ffmpeg on PATH, and the model:
  https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-multi-lang-v1_0.tar.bz2
  (unpack it and point KOKORO_DIR at the folder; default ~/.cache/kokoro/kokoro-multi-lang-v1_0)
speaker ids: af_heart=3, af_bella=2, af_nicole=6, am_michael=16, am_fenrir=14, am_puck=18
"""
import os
import base64, json, subprocess, sys, tempfile, time
from pathlib import Path
import numpy as np
import soundfile as sf
import sherpa_onnx as so

D = Path(os.environ.get("KOKORO_DIR", Path.home() / ".cache/kokoro/kokoro-multi-lang-v1_0"))
words_file, out_file, sid, vid, label = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
speed = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0

cfg = so.OfflineTtsConfig(model=so.OfflineTtsModelConfig(
    kokoro=so.OfflineTtsKokoroModelConfig(
        model=str(D / "model.onnx"), voices=str(D / "voices.bin"), tokens=str(D / "tokens.txt"),
        data_dir=str(D / "espeak-ng-data"), dict_dir=str(D / "dict"),
        lexicon=f"{D / 'lexicon-us-en.txt'},{D / 'lexicon-zh.txt'}"),
    num_threads=2, provider="cpu"))
tts = so.OfflineTts(cfg)


def synth(text):
    try:
        g = so.GenerationConfig(); g.sid, g.speed = sid, speed
        return tts.generate(text, g)
    except TypeError:
        return tts.generate(text, sid=sid, speed=speed)


def trim(x, sr, db=-45.0, head=0.01, tail=0.08):
    thr = np.abs(x).max() * (10 ** (db / 20))
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    return x[max(0, idx[0] - int(head * sr)): min(len(x), idx[-1] + int(tail * sr))]


words = [w["en"] for w in json.loads(Path(words_file).read_text(encoding="utf-8"))]
out = {}
t0 = time.time()
with tempfile.TemporaryDirectory() as td:
    for w in words:
        a = synth(w + ".")
        x = trim(np.asarray(a.samples, dtype=np.float32), a.sample_rate)
        x = x * (0.89 / (float(np.abs(x).max()) or 1.0))
        wav, mp3 = Path(td) / "w.wav", Path(td) / "w.mp3"
        sf.write(wav, x, a.sample_rate)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-ac", "1", "-ar", "24000",
                        "-b:a", "48k", str(mp3)], check=True)
        out[w] = {"d": round(len(x) / a.sample_rate, 3), "b64": base64.b64encode(mp3.read_bytes()).decode()}
        print(f"{w:12s} {out[w]['d']:.2f}s", file=sys.stderr, flush=True)
Path(out_file).write_text(json.dumps({"id": vid, "label": label, "words": out}, ensure_ascii=False, separators=(",", ":")),
                          encoding="utf-8")
ds = [v["d"] for v in out.values()]
print(json.dumps({"voice": vid, "words": len(out), "sec": round(time.time() - t0, 1), "min": min(ds), "max": max(ds),
                  "bytes": Path(out_file).stat().st_size}))
