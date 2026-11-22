#!/usr/bin/env python3
"""Add (or update) one unit's words in data/words.json from a TSV file.

TSV columns, tab-separated, one word per line (a header line starting with "no" is skipped):
    no  en  pos  pr  ko  ex
    1   giraffe  명사  저래프  기린  a tall giraffe (키 큰 기린)
- no  : number in the book (blank = next number)
- en  : English word or phrase (letters, space, ' . -)
- pos : 품사 (명사, 동사, 형용사, 부사, 구동사, 전치사, 대명사, 접속사, 감탄사, 숙어 ...)
- pr  : 실제 소리에 가까운 한글 발음 (예: bottle -> 바를, daughter -> 다러)
- ko  : 뜻
- ex  : 예시 표현 + 해석 (optional)

usage:
    python tools/add_words.py --unit 4 new_unit4.tsv            # upsert by word within unit 4
    python tools/add_words.py --unit 4 new_unit4.tsv --replace  # drop unit 4 first, then add
    python tools/add_words.py --unit 4 new_unit4.tsv --dry-run
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORDS = ROOT / "data/words.json"
EN_OK = re.compile(r"^[A-Za-z][A-Za-z' .\-]*$")
POS_KNOWN = {"명사", "동사", "형용사", "부사", "구동사", "전치사", "대명사", "접속사", "감탄사", "숙어", "조동사", "한정사"}
FIELDS = ["unit", "no", "en", "pos", "pr", "ko", "ex"]


def unit_key(u):
    return (0, int(u)) if str(u).isdigit() else (1, str(u))


def parse_unit(s):
    return int(s) if s.isdigit() else s


def read_tsv(path):
    rows = []
    for ln, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cols = [c.strip() for c in line.split("\t")]
        if ln == 1 and cols[0].lower() in ("no", "번호"):
            continue
        cols += [""] * (6 - len(cols))
        no, en, pos, pr, ko, ex = cols[:6]
        rows.append({"ln": ln, "no": int(no) if no.isdigit() else None, "en": re.sub(r"\s+", " ", en),
                     "pos": pos, "pr": pr, "ko": ko, "ex": ex})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv")
    ap.add_argument("--unit", required=True)
    ap.add_argument("--replace", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    unit = parse_unit(a.unit)

    words = json.loads(WORDS.read_text(encoding="utf-8"))
    rows = read_tsv(a.tsv)
    errors, warns = [], []
    for r in rows:
        if not EN_OK.match(r["en"]):
            errors.append(f"line {r['ln']}: English word looks wrong: {r['en']!r}")
        if not r["ko"]:
            errors.append(f"line {r['ln']}: missing meaning (ko) for {r['en']!r}")
        if r["pos"] and r["pos"] not in POS_KNOWN:
            warns.append(f"line {r['ln']}: unusual 품사 {r['pos']!r} for {r['en']!r}")
        if not r["pr"]:
            warns.append(f"line {r['ln']}: no 한글 발음 for {r['en']!r}")
    seen = {}
    for r in rows:
        k = r["en"].lower()
        if k in seen:
            errors.append(f"line {r['ln']}: {r['en']!r} repeats line {seen[k]}")
        seen[k] = r["ln"]
    if errors:
        print("\n".join(["ERRORS:"] + errors), file=sys.stderr)
        sys.exit(1)

    unit_words = [w for w in words if w["unit"] == unit and not a.replace]
    others = [w for w in words if w["unit"] != unit]
    by_en = {w["en"].lower(): w for w in unit_words}
    next_no = max([w["no"] for w in unit_words] + [0]) + 1
    added, updated = [], []
    for r in rows:
        k = r["en"].lower()
        if k in by_en:
            w = by_en[k]
            for f in ("pos", "pr", "ko", "ex"):
                if r[f]:
                    w[f] = r[f]
            if r["no"]:
                w["no"] = r["no"]
            updated.append(r["en"])
        else:
            no = r["no"] or next_no
            next_no = max(next_no, no + 1)
            w = {"unit": unit, "no": no, "en": r["en"], "pos": r["pos"], "pr": r["pr"], "ko": r["ko"], "ex": r["ex"]}
            unit_words.append(w); by_en[k] = w; added.append(r["en"])
    elsewhere = sorted({w["en"] for w in others if w["en"].lower() in by_en})
    if elsewhere:
        warns.append("also in other units (kept in both): " + ", ".join(elsewhere))

    merged = sorted(others + unit_words, key=lambda w: (unit_key(w["unit"]), w["no"]))
    nums = [w["no"] for w in unit_words]
    if len(nums) != len(set(nums)):
        warns.append(f"unit {unit}: duplicate numbers {sorted(n for n in set(nums) if nums.count(n) > 1)}")

    print(f"unit {unit}: +{len(added)} added, {len(updated)} updated, {len(unit_words)} words in unit, {len(merged)} total")
    if warns:
        print("\n".join(["WARNINGS:"] + warns))
    if a.dry_run:
        print("(dry run, nothing written)")
        return
    text = "[\n" + ",\n".join(json.dumps({f: w.get(f, "") for f in FIELDS}, ensure_ascii=False) for w in merged) + "\n]\n"
    WORDS.write_text(text, encoding="utf-8")
    missing = {}
    for vf in sorted((ROOT / "data/voices").glob("*.json")):
        pack = json.loads(vf.read_text(encoding="utf-8"))["words"]
        miss = [w["en"] for w in merged if w["en"].lower() not in pack]
        if miss:
            missing[vf.stem] = miss
    for vid, miss in missing.items():
        print(f"voice {vid}: {len(miss)} words without audio" + (f" e.g. {miss[:5]}" if miss else ""))
    if missing:
        print("next: python tools/gen_kokoro.py heart michael   (then python tools/build.py)")


if __name__ == "__main__":
    main()
