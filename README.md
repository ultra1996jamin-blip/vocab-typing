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

## 실행하는 법

`index.html`은 옆의 `data/` 파일을 읽어 와서, 더블클릭(file://)으로는 안 열려요. 아래 중 하나로 열어요.

- **웹 호스팅(GitHub Pages 등):** 저장소를 올리면 끝이에요. 새 단어는 파일을 푸시하면 바로 반영돼요.
- **로컬 서버:** 이 폴더에서 `python -m http.server 8000` 실행 후 `http://localhost:8000`
- **오프라인 단일 파일:** `python tools/build.py`로 `dist/vocab-typing-offline.html`을 만들면 더블클릭으로 열려요. 새 단어를 추가하면 다시 만들어야 해요.

## 폴더 구조

```
index.html              앱 (빌드 없음. 열릴 때 data/ 를 읽어 와요)
data/words.json         단어 목록 {unit, no, en, pos 품사, pr 한글 발음, ko 뜻, ex 예시}
data/audio/manifest.json  목소리 목록 {id, label, words: {단어: {d: 초, f: mp3 경로}}}
data/audio/<목소리>/*.mp3 단어별 원어민 음성
wordbook/*.xlsx         인쇄용 엑셀 단어장
tools/add_words.py      TSV → words.json (검증·단원별 병합)
tools/gen_kokoro.py     Kokoro 음성 팩 생성 (없는 단어만)
tools/build.py          (선택) 오프라인 단일 파일 dist/vocab-typing-offline.html 만들기
tools/audiolib.py       음성 파일·manifest 공용 함수
tools/make_wordbook.py  words.json → 엑셀 단어장
tools/test_app.py       헤드리스 브라우저 동작 검사
```

## 단어 추가하기 (사진 → 앱·단어장)

1. 단어장 사진에서 단어를 TSV로 옮겨요. 탭으로 구분하고, 열은 `no en pos pr ko ex` 순서예요.
   `pr`은 실제 소리에 가까운 한글 발음이에요. 예) bottle → 바를, daughter → 다러
   ```
   no	en	pos	pr	ko	ex
   1	giraffe	명사	저래프	기린	a tall giraffe (키 큰 기린)
   ```
2. `python tools/add_words.py --unit 4 unit4.tsv`를 실행해요. 같은 단원에 다시 넣으면 갱신되고, `--replace`를 붙이면 단원을 통째로 교체해요.
3. `python tools/gen_kokoro.py heart michael`를 실행해요. 음성이 없는 단어만 만들고, 모델이 없으면 `--download`를 붙여요.
4. 앱을 새로고침해요. **빌드는 필요 없어요.** 새 단원은 단원 선택에 자동으로 나와요.
5. `python tools/make_wordbook.py --units 4`를 실행하면 `wordbook/영어_단어장_Unit4.xlsx`가 생겨요. 인자 없이 실행하면 전체가 나와요.
6. `python tools/test_app.py`로 검사한 뒤 커밋해요.

선택한 목소리에 없는 단어는 다른 내장 목소리로 읽어요. 어느 목소리에도 없을 때만 브라우저 TTS로 읽어요.
Supertonic 목소리(`data/audio/supertonic/`)는 Supertonic 3(sherpa-onnx)로 만든 이전 목소리예요. 새 단어는 Kokoro 목소리만 만들면 돼요.

## 검사

```
pip install playwright && playwright install chromium
python tools/test_app.py
```
300타로 Unit 1을 쳤을 때 발음이 입력보다 늦게 끝난 횟수(`late`)가 0이어야 해요.
