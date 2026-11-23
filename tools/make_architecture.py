#!/usr/bin/env python3
"""Generate docs/architecture.drawio (4 pages): DFD level 0, DFD level 1, sequence (authoring), sequence (runtime).

    python tools/make_architecture.py          # writes docs/architecture.drawio
    python tools/make_architecture.py --png    # also writes a rough preview PNG per page (needs Pillow + Noto CJK)

Arrow colour/dash = protocol, arrow head = data direction (see the legend on every page).
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# protocol kinds: key -> (colour, extra style, legend text)
KINDS = {
    "https":   ("#1a73e8", "", "HTTPS (웹 · 채팅)"),
    "git":     ("#188038", "", "Git over HTTPS (push)"),
    "kbd":     ("#e8710a", "", "키보드 입력 (USB HID → keydown)"),
    "screen":  ("#00897b", "", "화면 렌더링 (DOM/CSS)"),
    "audio":   ("#9334e6", "dashed=1;dashPattern=1 3;", "오디오 출력 (HTMLAudio → 스피커)"),
    "file":    ("#5f6368", "dashed=1;dashPattern=8 4;", "로컬 파일 I/O · CLI/함수 호출"),
    "storage": ("#c5221f", "dashed=1;dashPattern=4 2 1 2;", "Web Storage API (localStorage)"),
    "mem":     ("#8d6e63", "dashed=1;dashPattern=2 2;", "메모리 접근 (Blob/Audio 객체)"),
}
SHORT = {"https": "HTTPS", "git": "Git/HTTPS", "kbd": "키보드(HID)", "screen": "화면(DOM)", "audio": "오디오(스피커)",
         "file": "파일 I/O·CLI", "storage": "localStorage", "mem": "메모리"}

STY_ENT = "rounded=0;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=13;fontStyle=1;"
STY_PROC = "rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=12;verticalAlign=top;"
STY_STORE = "shape=partialRectangle;whiteSpace=wrap;html=1;left=0;right=0;fillColor=#f5f5f5;strokeColor=#666666;fontSize=12;"
STY_ZONE = ("rounded=1;arcSize=3;whiteSpace=wrap;html=1;fillColor=none;dashed=1;strokeColor=#9aa0a6;strokeWidth=2;"
            "verticalAlign=top;align=left;spacingLeft=12;spacingTop=6;fontStyle=1;fontSize=13;fontColor=#5f6368;")
STY_NOTE = "shape=note;whiteSpace=wrap;html=1;size=14;fillColor=#fff9c4;strokeColor=#bfae3c;fontSize=12;align=left;spacingLeft=8;"
STY_LIFE = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=12;fontStyle=1;"
STY_FRAME = "rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#9aa0a6;dashed=1;verticalAlign=top;align=left;spacingLeft=6;fontSize=11;fontColor=#5f6368;"


class Page:
    def __init__(self, name, w, h):
        self.name, self.w, self.h = name, w, h
        self.nodes, self.edges, self.n = [], [], 1

    def _id(self, p):
        self.n += 1
        return f"{p}{self.n}"

    def node(self, label, x, y, w, h, style, nid=None):
        nid = nid or self._id("n")
        self.nodes.append(dict(id=nid, label=label, x=x, y=y, w=w, h=h, style=style))
        return nid

    def geo(self, nid):
        return next(n for n in self.nodes if n["id"] == nid)

    def edge(self, src, dst, a, b, label, kind, pts=(), dx=0, dy=-12, ret=False, lw=2, end=None):
        """Edge between two shapes. a/b are absolute points on the source/target border; pts are waypoints."""
        col, extra, _ = KINDS[kind]
        head = end or ("open" if ret else "block")
        extra = extra if not ret or "dashed" in extra else extra + "dashed=1;dashPattern=8 4;"
        style = (f"endArrow={head};endFill={0 if head == 'open' else 1};html=1;strokeColor={col};strokeWidth={lw};"
                 f"fontColor={col};fontSize=11;labelBackgroundColor=#ffffff;{extra}")
        self.edges.append(dict(id=self._id("e"), src=src, dst=dst, a=a, b=b, pts=list(pts), label=label, style=style,
                               dx=dx, dy=dy, kind=kind))

    def free_edge(self, a, b, label, kind, pts=(), dx=0, dy=-12, ret=False, lw=2, end=None):
        self.edge(None, None, a, b, label, kind, pts, dx, dy, ret, lw, end)

    # ---- xml
    def to_xml(self):
        d = ET.Element("diagram", name=self.name, id="pg_" + str(abs(hash(self.name)) % 10**8))
        m = ET.SubElement(d, "mxGraphModel", dx="1200", dy="800", grid="1", gridSize="10", guides="1", tooltips="1",
                          connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth=str(self.w),
                          pageHeight=str(self.h), math="0", shadow="0")
        r = ET.SubElement(m, "root")
        ET.SubElement(r, "mxCell", id="0")
        ET.SubElement(r, "mxCell", id="1", parent="0")
        for n in self.nodes:
            c = ET.SubElement(r, "mxCell", id=n["id"], value=n["label"], style=n["style"], vertex="1", parent="1")
            ET.SubElement(c, "mxGeometry", {"x": str(n["x"]), "y": str(n["y"]), "width": str(n["w"]),
                                            "height": str(n["h"]), "as": "geometry"})
        for e in self.edges:
            st = e["style"]
            attrs = dict(id=e["id"], value=e["label"], edge="1", parent="1")
            if e["src"]:
                s, t = self.geo(e["src"]), self.geo(e["dst"])
                fx = lambda g, p: min(1, max(0, (p[0] - g["x"]) / g["w"]))
                fy = lambda g, p: min(1, max(0, (p[1] - g["y"]) / g["h"]))
                st += (f"exitX={fx(s, e['a']):.4f};exitY={fy(s, e['a']):.4f};exitDx=0;exitDy=0;"
                       f"entryX={fx(t, e['b']):.4f};entryY={fy(t, e['b']):.4f};entryDx=0;entryDy=0;")
                attrs["source"], attrs["target"] = e["src"], e["dst"]
            attrs["style"] = st
            c = ET.SubElement(r, "mxCell", attrs)
            g = ET.SubElement(c, "mxGeometry", {"relative": "1", "as": "geometry"})
            if not e["src"]:
                ET.SubElement(g, "mxPoint", {"x": str(e["a"][0]), "y": str(e["a"][1]), "as": "sourcePoint"})
                ET.SubElement(g, "mxPoint", {"x": str(e["b"][0]), "y": str(e["b"][1]), "as": "targetPoint"})
            if e["pts"]:
                arr = ET.SubElement(g, "Array", {"as": "points"})
                for p in e["pts"]:
                    ET.SubElement(arr, "mxPoint", {"x": str(p[0]), "y": str(p[1])})
            if e["dx"] or e["dy"]:
                ET.SubElement(g, "mxPoint", {"x": str(e["dx"]), "y": str(e["dy"]), "as": "offset"})
        return d


def lab(kind, text):
    """Edge label: bold protocol tag + payload."""
    return f"<b>[{SHORT[kind]}]</b><br>{text}"


def legend(p, x, y, kinds, w=1180, extra_items=()):
    """Legend box: shape symbols + one sample arrow per protocol + direction rule."""
    rows = (len(kinds) + 1) // 2
    h = 70 + rows * 30 + (28 if extra_items else 0)
    p.node("<b>범례 (Legend)</b>", x, y, w, h, "rounded=1;arcSize=3;whiteSpace=wrap;html=1;fillColor=#ffffff;"
           "strokeColor=#9aa0a6;verticalAlign=top;align=left;spacingLeft=10;spacingTop=4;fontSize=13;")
    sx = x + 20
    if extra_items:
        for i, (label, style, ww) in enumerate(extra_items):
            p.node(label, sx, y + 34, ww, 24, style)
            sx += ww + 150
    base = y + 34 + (36 if extra_items else 0)
    for i, k in enumerate(kinds):
        col = x + 20 + (i % 2) * (w // 2)
        row = base + (i // 2) * 30
        p.free_edge((col, row + 12), (col + 90, row + 12), "", k, dy=0)
        p.node(f'<font color="{KINDS[k][0]}"><b>{SHORT[k]}</b></font> — {KINDS[k][2]}', col + 100, row, w // 2 - 130, 24,
               "text;html=1;align=left;verticalAlign=middle;fontSize=12;")
    p.node("화살표 머리(▶)가 가리키는 쪽이 <b>데이터가 흐르는 방향</b>이에요. 색·선 모양은 <b>프로토콜/인터페이스</b>를 뜻해요.",
           x + 20, y + h - 26, w - 40, 22, "text;html=1;align=left;verticalAlign=middle;fontSize=11;fontColor=#5f6368;")


# =====================================================================================
def dfd0():
    p = Page("1. DFD Level 0 (컨텍스트)", 1300, 800)
    p.node("<font style='font-size:16px'><b>영단어 타자 연습 시스템 — DFD Level 0 (컨텍스트 다이어그램)</b></font>", 20, 5, 900, 30,
           "text;html=1;align=left;verticalAlign=middle;")
    op = p.node("운영자<br><font style='font-size:11px;font-weight:normal'>(박진구 · 단어장 제공)</font>", 20, 60, 150, 140, STY_ENT)
    lr = p.node("학습자<br><font style='font-size:11px;font-weight:normal'>(타자 연습 사용자)</font>", 20, 330, 150, 190, STY_ENT)
    gh = p.node("GitHub<br><font style='font-size:11px;font-weight:normal'>저장소 + Pages(정적 호스팅)</font>", 1070, 205, 160, 130, STY_ENT)
    pr = p.node("<b>0</b><hr>영단어 타자 연습 시스템<br><font style='font-size:11px'>제작 도구(Claude 작업 환경)<br>+ 웹앱(학습자 브라우저)</font>",
                470, 60, 300, 460, STY_PROC + "fontSize=15;")
    # operator <-> system
    p.edge(op, pr, (170, 95), (470, 95), lab("https", "단어장 사진 · 단원 번호 · 추가 요청"), "https")
    p.edge(pr, op, (470, 165), (170, 165), lab("https", "엑셀 단어장 · 처리 결과 보고"), "https")
    # learner <-> system
    p.edge(lr, pr, (170, 370), (470, 370), lab("kbd", "타이핑 · 단축키(Enter/Tab/Esc) · 설정 조작"), "kbd")
    p.edge(pr, lr, (470, 430), (170, 430), lab("screen", "단어 · 뜻 · 키 안내 · 타수/정확도"), "screen")
    p.edge(pr, lr, (470, 485), (170, 485), lab("audio", "원어민 발음 1회 (속도 자동 맞춤)"), "audio")
    # system <-> github
    p.edge(pr, gh, (770, 245), (1070, 245), lab("git", "git push · 앱 코드 · 단어(JSON) · 음성(MP3)"), "git")
    p.edge(gh, pr, (1070, 305), (770, 305), lab("https", "HTTPS GET · index.html · words.json · manifest · mp3"), "https")
    p.node("※ 음성(MP3)은 <b>Claude가 제작 환경에서 Kokoro TTS로 미리 생성</b>해 저장소에 올려요.<br>"
           "학습자 브라우저는 음성을 <b>재생만</b> 하고, 서버 측 로직·DB는 없어요 (정적 파일만).",
           800, 400, 430, 90, STY_NOTE)
    legend(p, 20, 560, ["https", "git", "kbd", "screen", "audio"], w=1210,
           extra_items=[("외부 엔티티", STY_ENT, 110), ("프로세스", STY_PROC + "verticalAlign=middle;", 100)])
    return p


# =====================================================================================
def dfd1():
    p = Page("2. DFD Level 1", 1760, 1320)
    p.node("<font style='font-size:16px'><b>영단어 타자 연습 시스템 — DFD Level 1 (프로세스 분해)</b></font>", 20, 5, 900, 30,
           "text;html=1;align=left;verticalAlign=middle;")
    # zones (drawn first = behind)
    p.node("제작 환경 — Claude 클라우드 워크스페이스 (단어 추가 때만 실행)", 230, 50, 720, 840, STY_ZONE)
    p.node("실행 환경 — 학습자 브라우저 (정적 웹앱)", 1010, 50, 520, 840, STY_ZONE)
    op = p.node("운영자", 20, 150, 150, 240, STY_ENT)
    lr = p.node("학습자", 1590, 440, 150, 190, STY_ENT)
    gh = p.node("GitHub<br><font style='font-size:11px;font-weight:normal'>저장소 + Pages</font>", 270, 960, 220, 90, STY_ENT)

    def proc(i, title, sub, x, y):
        return p.node(f"<b>{i}</b><hr>{title}<br><font style='font-size:10px;color:#555'>{sub}</font>", x, y, 220, 90, STY_PROC)

    p11 = proc("1.1", "사진에서 단어 추출", "Claude 비전 → TSV", 270, 100)
    p12 = proc("1.2", "단어 검증 · 병합", "add_words.py", 270, 250)
    p13 = proc("1.3", "음성 생성", "gen_kokoro.py · Kokoro TTS + ffmpeg", 270, 400)
    p14 = proc("1.4", "엑셀 단어장 생성", "make_wordbook.py", 270, 550)
    p15 = proc("1.5", "저장소 반영 · 배포", "git commit/push → Pages", 270, 700)
    d1 = p.node("<b>D1</b> | data/words.json", 650, 265, 230, 60, STY_STORE)
    d1b = p.node("<b>D1</b> | words.json <font style='font-size:10px'>(참조)</font>", 650, 395, 230, 34, STY_STORE)
    d2 = p.node("<b>D2</b> | data/audio/*.mp3 + manifest.json", 650, 445, 230, 50, STY_STORE)
    d1c = p.node("<b>D1</b> | words.json <font style='font-size:10px'>(참조)</font>", 650, 550, 230, 34, STY_STORE)
    d3 = p.node("<b>D3</b> | wordbook/*.xlsx", 650, 595, 230, 45, STY_STORE)

    p16 = p.node("<b>1.6</b><hr>데이터 로딩 · 음성 미리 캐시<br><font style='font-size:10px;color:#555'>fetch · Blob · 미리 로딩(기본 5개)</font>",
                 1040, 130, 220, 90, STY_PROC)
    p17 = p.node("<b>1.7</b><hr>타자 연습 진행<br><font style='font-size:10px;color:#555'>입력 판정 · 타수 계산 · 발화 속도 맞춤</font>",
                 1040, 450, 220, 110, STY_PROC)
    p18 = p.node("<b>1.8</b><hr>설정 저장 · 복원", 1040, 730, 220, 80, STY_PROC)
    d5 = p.node("<b>D5</b> | 음성 캐시 (메모리)", 1330, 145, 190, 60, STY_STORE)
    d4 = p.node("<b>D4</b> | localStorage 설정", 1330, 740, 190, 60, STY_STORE)

    # ---- authoring flows
    p.edge(op, p11, (170, 190), (270, 125), lab("https", "단어장 사진 · 단원"), "https", pts=[(220, 190), (220, 125)], dx=-5, dy=-40)
    p.edge(p11, p12, (380, 190), (380, 250), "<b>[CLI]</b> TSV", "file", dx=40, dy=0)
    p.edge(p12, d1, (490, 295), (650, 295), lab("file", "쓰기 · 단원별 병합"), "file")
    p.edge(d1b, p13, (650, 412), (490, 412), lab("file", "읽기 · 음성 없는 단어"), "file")
    p.edge(p13, d2, (490, 470), (650, 470), lab("file", "쓰기 · MP3 + 길이(d)"), "file")
    p.edge(d1c, p14, (650, 567), (490, 567), lab("file", "읽기 · 전체 단어"), "file")
    p.edge(p14, d3, (490, 620), (650, 620), lab("file", "쓰기 · .xlsx"), "file", dy=-14)
    p.edge(p14, op, (270, 600), (95, 390), lab("https", "엑셀 단어장 · 결과 보고"), "https", pts=[(95, 600)], dx=-20, dy=-14)
    p.edge(d1, p15, (880, 280), (490, 730), lab("file", "읽기 · git add"), "file", pts=[(920, 280), (920, 730)], dx=-210, dy=-16)
    p.edge(d2, p15, (880, 470), (490, 760), lab("file", "읽기 · git add"), "file", pts=[(900, 470), (900, 760)], dx=-190, dy=16)
    p.edge(p15, gh, (380, 790), (380, 960), lab("git", "git push (코드 · JSON · MP3)"), "git", dx=100, dy=0)
    # ---- delivery GitHub -> browser
    p.edge(gh, p16, (490, 1005), (1040, 175), lab("https", "HTTPS GET · index.html · words.json · manifest · mp3"), "https",
           pts=[(990, 1005), (990, 175)], dx=-170, dy=0)
    # ---- runtime flows
    p.edge(p16, d5, (1260, 175), (1330, 175), lab("mem", "Blob"), "mem", dy=-26)
    p.edge(p16, p17, (1150, 220), (1100, 450), lab("mem", "단어 목록 · 목소리 정보"), "mem", dx=-70, dy=0)
    p.edge(d5, p17, (1425, 205), (1230, 450), lab("mem", "읽기 · 캐시된 음성"), "mem", dx=-10, dy=0)
    p.edge(p17, d5, (1245, 450), (1380, 205), "", "mem", end="none", lw=0)  # placeholder removed below
    p.edges.pop()
    p.edge(p18, p17, (1100, 730), (1100, 560), lab("mem", "설정값(목표 타수 등)"), "mem", dx=-75, dy=0)
    p.edge(p17, p18, (1190, 560), (1190, 730), lab("mem", "변경된 설정"), "mem", dx=55, dy=0)
    p.edge(p18, d4, (1260, 760), (1330, 760), lab("storage", "쓰기"), "storage", dy=-26)
    p.edge(d4, p18, (1330, 790), (1260, 790), lab("storage", "읽기"), "storage", dy=26)
    p.edge(lr, p17, (1590, 475), (1260, 475), lab("kbd", "타이핑 · 단축키 · 설정 조작"), "kbd", dy=-24)
    p.edge(p17, lr, (1260, 520), (1590, 520), lab("screen", "단어 · 뜻 · 키 안내 · 통계"), "screen", dy=-24)
    p.edge(p17, lr, (1260, 545), (1590, 575), lab("audio", "원어민 발음 1회"), "audio", dy=22)
    legend(p, 20, 1085, ["https", "git", "kbd", "screen", "audio", "file", "mem", "storage"], w=1720,
           extra_items=[("외부 엔티티", STY_ENT, 110), ("프로세스", STY_PROC + "verticalAlign=middle;", 100),
                        ("데이터 저장소", STY_STORE, 130)])
    return p


# =====================================================================================
def seq_page(name, title, lifelines, x0, step, top, bottom_pad=60):
    """lifelines: list of (label, width). Returns (page, xcenter list)."""
    xs, x = [], x0
    for lbl, w in lifelines:
        xs.append(x + w // 2)
        x += w + 40
    return xs


def seq_author():
    ll = [("운영자", 130), ("Claude<br>(에이전트)", 150), ("도구 스크립트<br>add_words · gen_kokoro<br>make_wordbook", 190),
          ("Kokoro TTS + ffmpeg", 170), ("로컬 Git<br>(작업 저장소)", 150), ("GitHub<br>저장소 / Pages", 150)]
    xs = seq_page("", "", ll, 40, 0, 0)
    H = 1330
    p = Page("3. 시퀀스 — 단어 추가(제작)", sum(w for _, w in ll) + 40 * 7, H)
    p.node("<font style='font-size:16px'><b>시퀀스 다이어그램 — 단어장 사진 → 앱 반영 (제작 흐름)</b></font>", 20, 5, 900, 30,
           "text;html=1;align=left;verticalAlign=middle;")
    top = 50
    x = 40
    for (lbl, w), cx in zip(ll, xs):
        p.node(lbl, x, top, w, 56, STY_LIFE)
        p.free_edge((cx, top + 56), (cx, H - 200), "", "file", dy=0, lw=1, end="none")
        p.edges[-1]["style"] = "endArrow=none;html=1;strokeColor=#9aa0a6;strokeWidth=1;dashed=1;dashPattern=6 4;"
        x += w + 40
    X = dict(op=xs[0], cl=xs[1], tool=xs[2], tts=xs[3], git=xs[4], gh=xs[5])
    y = top + 100

    def msg(a, b, text, kind, ret=False, gap=62, dy=-14):
        nonlocal y
        p.free_edge((X[a], y), (X[b], y), text, kind, ret=ret, dy=dy)
        y += gap

    def selfm(a, text, kind, h=34, gap=78):
        nonlocal y
        x = X[a]
        p.free_edge((x, y), (x, y + h), text, kind, pts=[(x + 70, y), (x + 70, y + h)], dx=130, dy=-h // 2)
        y += gap

    msg("op", "cl", lab("https", "① 단어장 사진 업로드 · 단원 번호"), "https")
    selfm("cl", "② 사진 판독 → TSV<br>(번호·단어·품사·발음·뜻·예시)", "file")
    msg("cl", "tool", lab("file", "③ add_words.py --unit N (TSV)"), "file")
    msg("tool", "cl", lab("file", "④ 검증 결과 · words.json 병합 · 음성 없는 단어"), "file", ret=True)
    msg("cl", "tool", lab("file", "⑤ gen_kokoro.py heart michael"), "file")
    msg("tool", "tts", lab("file", "⑥ 단어마다 합성 요청 (sid · speed)"), "file")
    msg("tts", "tool", lab("file", "⑦ wav → 무음 제거 → MP3 48kbps"), "file", ret=True)
    msg("tool", "cl", lab("file", "⑧ data/audio/*.mp3 · manifest.json 갱신"), "file", ret=True)
    msg("cl", "tool", lab("file", "⑨ make_wordbook.py → 엑셀 단어장"), "file")
    msg("cl", "tool", lab("file", "⑩ test_app.py (헤드리스 브라우저 검증)"), "file", gap=66)
    msg("cl", "git", lab("file", "⑪ git add · commit"), "file")
    msg("git", "gh", lab("git", "⑫ git push origin main"), "git")
    selfm("gh", "⑬ Pages 빌드 · 배포<br>(약 1~2분)", "https")
    msg("cl", "op", lab("https", "⑭ 엑셀 단어장 + 완료 보고 (앱은 새로고침으로 반영)"), "https", ret=True)
    legend(p, 20, H - 190, ["https", "git", "file"], w=p.w - 40,
           extra_items=[("동기 호출  ───▶", "text;html=1;align=left;fontSize=12;", 120),
                        ("응답/반환  ‒ ‒ ▷ (점선 + 열린 화살표)", "text;html=1;align=left;fontSize=12;", 280),
                        ("자기 호출  ↺", "text;html=1;align=left;fontSize=12;", 100)])
    return p


def seq_run():
    ll = [("학습자", 120), ("앱 (index.html)<br>브라우저", 170), ("GitHub Pages<br>(정적 호스팅)", 160),
          ("음성 캐시<br>(메모리 Blob/Audio)", 170), ("localStorage", 140)]
    xs = seq_page("", "", ll, 40, 0, 0)
    H = 1800
    p = Page("4. 시퀀스 — 학습 실행", sum(w for _, w in ll) + 40 * 6, H)
    p.node("<font style='font-size:16px'><b>시퀀스 다이어그램 — 타자 연습 실행 (로딩 → 발음 → 입력 → 다음 단어)</b></font>", 20, 5, 900, 30,
           "text;html=1;align=left;verticalAlign=middle;")
    top, x = 50, 40
    for (lbl, w), cx in zip(ll, xs):
        p.node(lbl, x, top, w, 56, STY_LIFE)
        p.free_edge((cx, top + 56), (cx, H - 200), "", "file", dy=0, lw=1, end="none")
        p.edges[-1]["style"] = "endArrow=none;html=1;strokeColor=#9aa0a6;strokeWidth=1;dashed=1;dashPattern=6 4;"
        x += w + 40
    X = dict(u=xs[0], app=xs[1], pg=xs[2], ca=xs[3], ls=xs[4])
    y = top + 100

    def msg(a, b, text, kind, ret=False, gap=62, dy=-14):
        nonlocal y
        p.free_edge((X[a], y), (X[b], y), text, kind, ret=ret, dy=dy)
        y += gap

    def selfm(a, text, kind, h=34, gap=78):
        nonlocal y
        x = X[a]
        p.free_edge((x, y), (x, y + h), text, kind, pts=[(x + 70, y), (x + 70, y + h)], dx=130, dy=-h // 2)
        y += gap

    msg("u", "app", lab("https", "① URL 접속 (페이지 열기)"), "https")
    msg("app", "pg", lab("https", "② GET index.html"), "https")
    msg("pg", "app", lab("https", "200 · HTML/JS"), "https", ret=True)
    msg("app", "pg", lab("https", "③ GET data/words.json · audio/manifest.json (no-cache)"), "https")
    msg("pg", "app", lab("https", "200 · JSON (단어 · 목소리 목록)"), "https", ret=True)
    msg("app", "ls", lab("storage", "④ getItem(설정)"), "storage")
    msg("ls", "app", lab("storage", "저장된 설정 (없으면 기본값)"), "storage", ret=True)
    msg("u", "app", lab("kbd", "⑤ Enter (연습 시작)"), "kbd")
    msg("app", "pg", lab("https", "⑥ GET 현재 + 다음 N개 mp3 (병렬 · N=미리 로딩)"), "https")
    msg("pg", "app", lab("https", "200 · audio/mpeg"), "https", ret=True)
    msg("app", "ca", lab("mem", "⑦ Blob URL로 보관 (Audio 객체)"), "mem")
    msg("app", "u", lab("audio", "⑧ 새 단어 표시 + 원어민 발음 1회 (playbackRate 자동 계산)"), "audio", gap=70)
    loop_top = y - 52
    msg("u", "app", lab("kbd", "⑨ 첫 글자 입력 → 타수 측정 시작"), "kbd")
    selfm("app", "⑩ 입력 판정 · 다음 키 표시<br>· 타수 = (타수−1)/시간", "screen", gap=84)
    msg("u", "app", lab("kbd", "⑪ 마지막 글자 입력 (단어 완료)"), "kbd")
    msg("app", "ca", lab("mem", "⑫ 다음 단어 음성 조회 + 미리 로딩 보충"), "mem")
    msg("ca", "app", lab("mem", "Audio 객체 (이미 준비된 경우 즉시)"), "mem", ret=True)
    msg("app", "pg", lab("https", "(캐시에 없을 때만) GET mp3"), "https")
    msg("app", "u", lab("audio", "⑬ 다음 단어 + 발음 1회"), "audio")
    loop_bot = y - 20
    p.node("loop [단어 반복]", 30, loop_top, sum(w for _, w in ll) + 40 * 5 + 20, loop_bot - loop_top, STY_FRAME)
    y += 10
    msg("u", "app", lab("kbd", "⑭ 설정 변경 (목표 타수 · 목소리 · 여유 비율 …)"), "kbd")
    msg("app", "ls", lab("storage", "setItem(설정)"), "storage")
    msg("app", "u", lab("screen", "⑮ 결과 화면 (평균/최고 타수 · 정확도 · 발음 늦게 끝난 횟수)"), "screen")
    legend(p, 20, H - 190, ["https", "kbd", "screen", "audio", "mem", "storage"], w=p.w - 40,
           extra_items=[("동기 호출  ───▶", "text;html=1;align=left;fontSize=12;", 120),
                        ("응답/반환  ‒ ‒ ▷ (점선 + 열린 화살표)", "text;html=1;align=left;fontSize=12;", 280),
                        ("자기 호출  ↺", "text;html=1;align=left;fontSize=12;", 100)])
    return p


def main():
    pages = [dfd0(), dfd1(), seq_author(), seq_run()]
    mx = ET.Element("mxfile", host="app.diagrams.net", agent="claude", version="24.0.0")
    for pg in pages:
        mx.append(pg.to_xml())
    ET.indent(mx)
    out = ROOT / "docs/architecture.drawio"
    out.parent.mkdir(exist_ok=True)
    ET.ElementTree(mx).write(out, encoding="utf-8", xml_declaration=True)
    print(out, f"{out.stat().st_size:,} bytes", [(p.name, len(p.nodes), len(p.edges)) for p in pages])
    if "--png" in sys.argv:
        preview(pages)


def preview(pages):
    """Very rough rendering of my own geometry (not draw.io) to spot overlaps."""
    import re
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 11)
    out = ROOT / "tools/shots"
    out.mkdir(exist_ok=True)
    strip = lambda s: re.sub(r"<[^>]+>", " ", s.replace("<br>", "\n").replace("<hr>", "\n")).replace("  ", " ").strip()
    for i, pg in enumerate(pages, 1):
        im = Image.new("RGB", (pg.w, pg.h), "white")
        d = ImageDraw.Draw(im)
        for n in pg.nodes:
            d.rectangle([n["x"], n["y"], n["x"] + n["w"], n["y"] + n["h"]], outline="#888")
            d.multiline_text((n["x"] + 4, n["y"] + 3), strip(n["label"]), fill="black", font=f)
        for e in pg.edges:
            col = KINDS[e["kind"]][0] if "strokeColor=#9aa0a6" not in e["style"] else "#bbb"
            path = [e["a"]] + e["pts"] + [e["b"]]
            d.line(path, fill=col, width=2)
            bx, by = e["b"]
            d.ellipse([bx - 3, by - 3, bx + 3, by + 3], fill=col)
            if e["label"]:
                mid = path[len(path) // 2] if len(path) > 2 else ((path[0][0] + path[1][0]) / 2, (path[0][1] + path[1][1]) / 2)
                tx, ty = mid[0] + e["dx"], mid[1] + e["dy"]
                t = strip(e["label"])
                bb = d.multiline_textbbox((tx, ty), t, font=f, anchor="mm", align="center")
                d.rectangle(bb, fill="white")
                d.multiline_text((tx, ty), t, fill=col, font=f, anchor="mm", align="center")
        im.save(out / f"arch_{i}.png")
    print("previews in", out)


if __name__ == "__main__":
    main()
