#!/usr/bin/env python3
"""Headless browser check: typing flow, speed (from first keystroke), key hints, voices, settings.
Run from anywhere:  python tools/test_app.py   (needs: pip install playwright && playwright install chromium)
"""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = (ROOT / 'index.html').as_uri()
shots = ROOT / 'tools' / 'shots'; shots.mkdir(exist_ok=True)
errors = []
ev = lambda page, js: page.evaluate(js)

with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    page = b.new_page(viewport={'width': 1440, 'height': 900})
    page.on('pageerror', lambda e: errors.append('pageerror: ' + str(e)))
    page.on('console', lambda m: errors.append('console: ' + m.text) if m.type == 'error' else None)
    page.goto(URL); page.wait_for_timeout(800)
    print('voices:', ev(page, 'VOICES.map(v=>v.id+":"+Object.keys(v.words).length)'), 'default:', ev(page, 'S.voice'))
    print('start info:', page.inner_text('#startInfo').replace('\n', ' | '))
    page.screenshot(path=str(shots / 'a_start.png'))

    page.click('#startBtn'); page.wait_for_timeout(150)
    print('word:', ev(page, 'cur.en'), 'playing:', ev(page, 'playing && playing.audio ? !playing.audio.paused : null'),
          'next key:', ev(page, "[...document.querySelectorAll('.key.next')].map(k=>k.dataset.id)"))
    # wait 1s before first key -> must NOT count toward speed
    page.wait_for_timeout(1000)
    page.keyboard.type('bottle', delay=200); page.wait_for_timeout(30)
    print('after bottle: last tpm', ev(page, 'st.last'), '(expect ~300 since reaction time excluded)')
    page.keyboard.type('bx', delay=200)
    print('typo -> next key:', ev(page, "[...document.querySelectorAll('.key.next')].map(k=>k.dataset.id)"),
          'entry err class:', ev(page, "el.entry.classList.contains('err')"))
    page.wait_for_timeout(60)
    page.screenshot(path=str(shots / 'b_typo.png'))
    page.keyboard.press('Backspace'); page.keyboard.type('owl', delay=200)
    page.keyboard.insert_text('ㅎ'); page.wait_for_timeout(30)
    print('hangul hint:', page.inner_text('#hint'))
    while ev(page, 'running') and ev(page, 'idx') < 20:
        page.wait_for_timeout(250)                      # reaction pause between words
        page.keyboard.type(ev(page, 'cur.en'), delay=200)
    print('Unit1 @300: late=%s avg=%s best=%s acc=%s' % (ev(page, 'st.late'), ev(page, 'Math.round(st.strokes/st.time*60)'),
          ev(page, 'st.best'), page.inner_text('#stAcc')))
    print('side info:', page.inner_text('#info').replace('\n', ' | '))
    page.keyboard.type(ev(page, 'cur.en')[:2], delay=200)
    page.screenshot(path=str(shots / 'c_typing.png'))

    # shift hint for capital letter (custom word)
    # level pill
    page.click('.lv[data-v="500"]'); page.wait_for_timeout(50)
    print('level ->', ev(page, 'S.tpm'), 'pill on:', ev(page, "document.querySelector('.lv.on').dataset.v"))
    # voice switch to michael
    ev(page, "S.voice='michael'; saveSettings();")
    page.keyboard.press('Tab'); page.wait_for_timeout(100)
    print('replay with michael playing:', ev(page, 'playing && playing.audio ? !playing.audio.paused : null'), ev(page, 'lastPlan.dur'))
    # settings modal
    page.click('#openSettings'); page.wait_for_timeout(150)
    page.screenshot(path=str(shots / 'd_settings.png'))
    print('voice options:', ev(page, "[...document.querySelectorAll('[data-k=voice] option')].map(o=>o.textContent)"))
    page.click('#closeSettings2'); page.wait_for_timeout(100)
    # finish all quickly
    while ev(page, 'running'):
        page.keyboard.type(ev(page, 'cur.en')[ev(page, 'el.entry.value.length'):], delay=40)
    page.wait_for_timeout(150)
    print('done:', page.inner_text('#result').replace('\n', ' '))
    page.screenshot(path=str(shots / 'e_done.png'))
    # narrow viewport
    page.set_viewport_size({'width': 820, 'height': 900}); page.keyboard.press('Enter'); page.wait_for_timeout(200)
    page.screenshot(path=str(shots / 'f_narrow.png'))
    b.close()
print('ERRORS:', errors or 'none')
