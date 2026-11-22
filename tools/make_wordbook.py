#!/usr/bin/env python3
"""Make a printable Excel 단어장 from data/words.json.

usage:
    python tools/make_wordbook.py                 # all units -> wordbook/영어_단어장_Unit1-3.xlsx
    python tools/make_wordbook.py --units 4       # one unit  -> wordbook/영어_단어장_Unit4.xlsx
    python tools/make_wordbook.py --units 4 5 -o out.xlsx
Sheets: '전체' (when more than one unit) + one sheet per unit.
Columns: 번호 · 단어 · 품사 · 발음 · 뜻 · 예시. A4 portrait, fits one page wide, header repeats.
"""
import argparse, json
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

ROOT = Path(__file__).resolve().parent.parent
FONT = "맑은 고딕"
ACCENT, BAND = "E17F5E", "FBEDE8"
thin = Side(style="thin", color="D9C9C3")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)


def ukey(u):
    return (0, int(u)) if str(u).isdigit() else (1, str(u))


def label(u):
    return f"Unit {u}" if str(u).isdigit() else str(u)


def sheet(wb, title, heading, headers, rows, widths, word_col):
    ws = wb.create_sheet(title[:31])
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
    c = ws.cell(row=1, column=1, value=heading)
    c.font = Font(name=FONT, size=16, bold=True, color="8A3B22")
    c.alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 30
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=3, column=i, value=h)
        c.font = Font(name=FONT, size=11, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=ACCENT)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = BORDER
    for r, row in enumerate(rows, 4):
        for i, v in enumerate(row, 1):
            c = ws.cell(row=r, column=i, value=v)
            c.border = BORDER
            c.font = Font(name=FONT, size=12 if i == word_col else 11, bold=(i == word_col))
            left = headers[i - 1] in ("뜻", "예시")
            c.alignment = Alignment(horizontal="left" if left else "center", vertical="center", wrap_text=True)
            if (r - 4) % 2:
                c.fill = PatternFill("solid", fgColor=BAND)
        ws.row_dimensions[r].height = 22
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(65 + i)].width = w
    ws.freeze_panes = "A4"
    ws.print_title_rows = "3:3"
    ws.page_setup.orientation = "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_options.horizontalCentered = True
    ws.page_margins.left = ws.page_margins.right = 0.4
    return ws


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", nargs="*")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    words = json.loads((ROOT / "data/words.json").read_text(encoding="utf-8"))
    all_units = sorted({w["unit"] for w in words}, key=ukey)
    units = [u for u in all_units if not a.units or str(u) in a.units]
    if not units:
        raise SystemExit(f"no such unit; have {all_units}")
    sel = [w for w in words if w["unit"] in units]
    name = f"{label(units[0])}-{units[-1]}" if len(units) > 1 else label(units[0])
    out = Path(a.out) if a.out else ROOT / "wordbook" / f"영어_단어장_{name.replace(' ', '')}.xlsx"
    out.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook(); wb.remove(wb.active)
    if len(units) > 1:
        ws = sheet(wb, "전체", f"영어 단어장 {name} (전체 {len(sel)}단어)", ["단원", "번호", "단어", "품사", "발음", "뜻", "예시"],
                   [(label(w["unit"]), w["no"], w["en"], w.get("pos", ""), w.get("pr", ""), w["ko"], w.get("ex", "")) for w in sel],
                   [9, 7, 15, 9, 14, 24, 42], word_col=3)
        ws.auto_filter.ref = f"A3:G{3 + len(sel)}"
    for u in units:
        uw = [w for w in sel if w["unit"] == u]
        sheet(wb, label(u), f"영어 단어장 {label(u)}", ["번호", "단어", "품사", "발음", "뜻", "예시"],
              [(w["no"], w["en"], w.get("pos", ""), w.get("pr", ""), w["ko"], w.get("ex", "")) for w in uw],
              [7, 15, 9, 14, 24, 42], word_col=2)
    wb.save(out)
    print(f"{out} · {len(sel)} words · sheets: {wb.sheetnames}")


if __name__ == "__main__":
    main()
