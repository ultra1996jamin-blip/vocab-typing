# 영단어 타자 연습 (vocab-typing)

영어 단어를 키보드로 치면서 외우는 가벼운 웹앱이에요. 화면은 한컴타자 낱말연습과 비슷하게 만들었어요. 새 단어가 나오면 원어민 발음을 들려주고, 목표 타수로 쳐도 단어를 다 치기 전에 발음이 끝나도록 재생 속도를 맞춰요.

- 실행: `index.html`을 브라우저로 열면 돼요. 서버도 인터넷도 필요 없어요. 음성까지 파일 하나에 들어 있어요.
- 게시본: https://claude.ai/artifact/McdJv8dUMpSsGaz25dt6BF

## 기능

| 기능 | 내용 |
| --- | --- |
| 원어민 발음 | 미리 만든 미국식 음성 3종: Kokoro Heart(여자, 기본), Kokoro Michael(남자), Supertonic(여자). 내장 음성이 없는 단어는 브라우저 TTS로 읽어요 |
| 미리 로딩 | 지금 단어와 다음 N개(기본 5개)의 발음을 메모리에 미리 올려 바로 재생해요 |
| 속도 맞춤 | 도전단계(목표 타수) 기준 입력 시간 × 여유 비율 − 지연 보정 안에 끝나도록 재생 속도를 올려요. 피치는 유지돼요 |
| 타수 계산 | 단어마다 첫 타부터 마지막 타까지의 시간으로 계산해요. `(타수 − 1) ÷ 시간`이라 단어가 뜬 뒤 반응 시간은 빠져요 |
| 화면 | 단원 선택, 진행중 통계(시간·타수·정확도·오타), 다음 단어 미리 보기, 도전단계, 다음 키를 표시하는 화상 키보드 |
| 설정 | 목소리, 발음 횟수, 볼륨, 목표 타수, 자동 속도 맞춤, 여유 비율, 지연 보정, 기본·최대 속도, 미리 로딩 개수, 넘어가기 방식, 오타 처리, 순서, 표시 항목, 내 단어. 설정은 브라우저(localStorage)에 저장돼요 |
| 단축키 | `Enter` 시작 · `Tab` 다시 듣기 · `Esc` 멈추기 |

## 폴더 구조

```
index.html              빌드 결과물 (이 파일만 있으면 실행됨)
src/app.html            화면·로직 원본 (단어·음성 자리표시자 포함)
data/words.json         단어 목록 (unit, en, ko 뜻, pr 한글 발음)
data/voices/*.json      목소리별 음성 팩 {id, label, words: {단어: {d: 초, b64: mp3}}}
tools/build.py          src + data → index.html
tools/gen_kokoro.py     Kokoro로 음성 팩 생성
tools/test_app.py       헤드리스 브라우저 동작 검사
```

## 단어 추가하기

1. `data/words.json`에 단어를 넣어요. 예) `{"unit":4,"en":"giraffe","ko":"기린","pr":"저래프"}`
2. 음성 팩을 다시 만들어요. 모델 받는 법은 `tools/gen_kokoro.py` 맨 위에 적어 두었어요.
   ```
   python tools/gen_kokoro.py data/words.json data/voices/heart.json 3 heart "여자 · Heart (Kokoro, 추천)"
   python tools/gen_kokoro.py data/words.json data/voices/michael.json 16 michael "남자 · Michael (Kokoro)"
   ```
3. `python tools/build.py`를 실행해요. 음성이 없는 단어는 경고로 알려주고, 그 단어는 브라우저 TTS로 읽어요.
4. 새 단원을 쓰려면 `src/app.html`의 `UNIT_OPTS`에 항목을 추가해요.

Supertonic 팩(`data/voices/supertonic.json`)은 Supertonic 3(sherpa-onnx)로 만든 이전 목소리예요. 새 단어는 Kokoro 팩만 갱신해도 돼요.

## 검사

```
pip install playwright && playwright install chromium
python tools/test_app.py
```
300타로 Unit 1을 쳤을 때 발음이 입력보다 늦게 끝난 횟수(`late`)가 0이어야 해요.
