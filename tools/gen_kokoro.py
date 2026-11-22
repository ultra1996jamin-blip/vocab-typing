#!/usr/bin/env python3
"""Make or update Kokoro v1.0 voice packs (US English, offline) for the words in data/words.json.

By default only words missing from data/voices/<voice>.json are generated and merged in.

usage:
    python tools/gen_kokoro.py heart michael            # add audio for new words
    python tools/gen_kokoro.py heart --all              # regenerate every word
    python tools/gen_kokoro.py --download heart michael # fetch the model first if it is missing

needs: pip install sherpa-onnx numpy soundfile   and ffmpeg on PATH.
model: https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-multi-lang-v1_0.tar.bz2
       unpacked into KOKORO_DIR (default ~/.cache/kokoro/kokoro-multi-lang-v1_0)
pack format: {"id", "label", "words": {word_lowercase: {"d": seconds, "b64": mp3 base64}}}
"""
import argparse, base64, json, os, subprocess, sys, tarfile, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-multi-lang-v1_0.tar.bz2"
D = Path(os.environ.get("KOKORO_DIR", Path.home() / ".cache/kokoro/kokoro-multi-lang-v1_0"))
PRESETS = {  # voice id -> (Kokoro speaker id, label shown in the app)
    "heart":   (3,  "여자 · Heart (Kokoro, 추천)"),
    "michael": (16, "남자 · Michael (Kokoro)"),
    "bella":   (2,  "여자 · Bella (Kokoro)"),
    "nicole":  (6,  "여자 · Nicole (Kokoro)"),
    "fenrir":  (14, "남자 · Fenrir (Kokoro)"),
    "puck":    (18, "남자 · Puck (Kokoro)"),
}


def download():
    D.parent.mkdir(parents=True, exist_ok=True)
    tmp = D.parent / "kokoro.tar.bz2"
    print(f"downloading {MODEL_URL} ...", file=sys.stderr)
    urllib.request.urlretrieve(MODEL_URL, tmp)
    with tarfile.open(tmp) as t:
        t.extractall(D.parent)
    tmp.unlink()


def load_tts():
    import sherpa_onnx as so
    cfg = so.OfflineTtsConfig(model=so.OfflineTtsModelConfig(
        kokoro=so.OfflineTtsKokoroModelConfig(
            model=str(D / "model.onnx"), voices=str(D / "voices.bin"), tokens=str(D / "tokens.txt"),
            data_dir=str(D / "espeak-ng-data"), dict_dir=str(D / "dict"),
            lexicon=f"{D / 'lexicon-us-en.txt'},{D / 'lexicon-zh.txt'}"),
        num_threads=2, provider="cpu"))
    return so, so.OfflineTts(cfg)


def synth(so, tts, text, sid, speed):
    try:
        g = so.GenerationConfig(); g.sid, g.speed = sid, speed
        return tts.generate(text, g)
    except TypeError:
        return tts.generate(text, sid=sid, speed=speed)


def trim(np, x, sr, db=-45.0, head=0.01, tail=0.08):
    thr = np.abs(x).max() * (10 ** (db / 20))
    idx = np.where(np.abs(x) > thr)[0]
    return x if len(idx) == 0 else x[max(0, idx[0] - int(head * sr)): min(len(x), idx[-1] + int(tail * sr))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("voices", nargs="+", choices=sorted(PRESETS))
    ap.add_argument("--all", action="store_true", help="regenerate every word")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--download", action="store_true", help="download the model if missing")
    a = ap.parse_args()

    if not (D / "model.onnx").exists():
        if a.download:
            download()
        else:
            sys.exit(f"Kokoro model not found in {D}. Run with --download or set KOKORO_DIR.")
    import numpy as np
    import soundfile as sf
    so, tts = load_tts()

    words = [w["en"] for w in json.loads((ROOT / "data/words.json").read_text(encoding="utf-8"))]
    for vid in a.voices:
        sid, label = PRESETS[vid]
        f = ROOT / "data/voices" / f"{vid}.json"
        pack = json.loads(f.read_text(encoding="utf-8")) if f.exists() and not a.all else {"words": {}}
        pack.update({"id": vid, "label": label})
        todo = [w for w in dict.fromkeys(words) if w.lower() not in pack["words"]]
        t0 = time.time()
        with tempfile.TemporaryDirectory() as td:
            for w in todo:
                au = synth(so, tts, w + ".", sid, a.speed)
                x = trim(np, np.asarray(au.samples, dtype=np.float32), au.sample_rate)
                x = x * (0.89 / (float(np.abs(x).max()) or 1.0))
                wav, mp3 = Path(td) / "w.wav", Path(td) / "w.mp3"
                sf.write(wav, x, au.sample_rate)
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-ac", "1", "-ar", "24000",
                                "-b:a", "48k", str(mp3)], check=True)
                pack["words"][w.lower()] = {"d": round(len(x) / au.sample_rate, 3), "b64": base64.b64encode(mp3.read_bytes()).decode()}
                print(f"  {vid}: {w:14s} {pack['words'][w.lower()]['d']:.2f}s", file=sys.stderr, flush=True)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"id": vid, "label": label, "words": pack["words"]}, ensure_ascii=False, separators=(",", ":")),
                     encoding="utf-8")
        print(f"{vid}: +{len(todo)} generated in {time.time() - t0:.1f}s, {len(pack['words'])} words in pack")


if __name__ == "__main__":
    main()
