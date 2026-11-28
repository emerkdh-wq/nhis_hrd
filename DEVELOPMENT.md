# 메타버스 청풍 — 개발 인수인계 문서

국민건강보험공단 인재개발원(제천 청풍호) 운동장을 옮겨 놓은 힐링용 웹 메타버스입니다.
이 문서는 다른 사람(또는 다른 Claude 계정)이 이어서 개발할 때 먼저 읽는 안내서입니다.

- 사이트 주소: https://metahrd.space (GitHub Pages, 이 저장소의 `gh-pages` 브랜치를 그대로 보여 줌)
- 예전 주소: https://emerkdh-wq.github.io/nhis_hrd/ (metahrd.space로 자동 이동)
- 데이터: Firebase Realtime Database, 프로젝트 `NhisHRD` (아시아-동남아 리전)

---

## 1. 파일 구성

| 파일 | 내용 |
|---|---|
| `index.html` | **사이트 전부.** HTML·CSS·JS·셰이더가 한 파일에 들어 있다. 외부 라이브러리 없이 WebGL1을 직접 쓴다. |
| `bonkwan.glb` | 교육동(본관) 3D 모델 |
| `saenghwal.glb` | 북쪽 숙소동(생활관) 단지 모델 |
| `namdong.glb` | 남쪽 제2교육동(ㄱ자 동) 모델 |
| `cat_*.glb` | 예전에 시험한 고양이 모델. **지금은 안 쓴다** (`USE_CAT_MODELS = false`) |
| `CNAME` | 커스텀 도메인 `metahrd.space` |
| `tools/shot.py` | 헤드리스 크롬으로 화면을 찍어 확인하는 테스트 도구 |
| `tools/build_artifact.py` | `.glb`를 base64로 넣은 한 파일짜리 `artifact.html`을 만든다 (Claude 아티팩트처럼 파일을 따로 못 올리는 곳용) |

`model-src` 브랜치에는 모델을 만들 때 쓴 원본 사진이 있다.

**배포:** `index.html`을 고쳐 `gh-pages`에 푸시하면 1~2분 뒤 metahrd.space에 반영된다. 별도 빌드 과정은 없다.

---

## 2. 좌표와 지형

- 단위는 미터. **x = 동쪽(+), z = 남쪽(+)**, y = 위. 운동장 바닥 높이 0.04.
- 운동장(잔디) x −36~36, z −54~54. 축구장 선은 x ±32, z ±50. 골대는 z = ±50.
- 빨간 트랙은 운동장 둘레. 동쪽 트랙 바깥(x > 40.6)은 지형 함수 `H(x,z)`로 높이가 정해진다 (호숫가 풀밭은 약 −1.3).
- 바닥 높이는 `groundY(x,z)`를 쓴다.
- 캐릭터 이동 범위: x −38 ~ `maxX(z)`, z −55.4 ~ 55.4.
  `maxX(z)`는 기본 54.8이고, 북동쪽(z < −22)과 남동쪽(z > 38) 호숫가 풀밭만 64까지 갈 수 있다.
- 부딪히는 물체는 `SOLIDS` 배열에 `[x, z, 반지름]`으로 넣는다.
  **주의:** `SOLIDS`는 파일 중간(약 680줄)에서 `const`로 선언되므로, 그보다 위쪽 코드에서 push하면 TDZ 오류로 페이지 전체가 멈춘다.
- 청풍호 수면 높이는 `WATER = −6`.

### 주요 위치 상수

| 상수 | 위치 | 무엇 |
|---|---|---|
| `QM` | (−35.4, −53.2) 북서쪽 모서리 | 명언 뽑기 기계 |
| `GB_AT` | (34.5, 55.5) 남동쪽 끝 철망 | 방명록 게시판 |
| `TOMATO` | 동쪽 나무 줄 북쪽 끝 (약 47, −50) | 방울토마토 나무 |
| `CAIRN` | (57.3, −51.6) | 돌탑 (사람 키) |
| `BIKE` | 처음 (60.6, −36.8) | 버려진 자전거 (이후 위치는 Firebase에 저장) |
| `CLOVER` | (46.4, −2.2), 반지름 4.2 | 세잎클로버밭 |
| `TRAMP` | (58.6, 46.4), 반지름 1.55 | 매립형 트램펄린 |
| `CAT_HOME` | x 27~40, z −53.6~−37 | 고양이 '르샤'가 주로 머무는 북동쪽 구역 |
| `TCOURTS` | x 61~83 | 테니스장 3면 |
| `BENCHES` | 둘레 여러 곳 | 벤치 (최대 2명, 혼자면 가운데) |
| `VIEWS` | — | 방향별 안내 문구(북/북동/…/북서) |

---

## 3. 코드 구조 (index.html 안)

위에서부터 대략 이런 순서다.

1. **CSS·HTML**: 상단 시계·날씨, 버튼(설정/소리/눕기/쉬기), 아래쪽 동작 버튼(`#bSit` 하나를 상황에 따라 다른 이름으로 씀, `#bWave` 손 흔들기, `#bJump` 점프), 시작 화면(`#gate`), 대기열(`#queue`), 방명록(`#gbook`), 명언 카드(`#quote`).
2. **WebGL 기초**: `Mesh` 클래스(`box`, `cyl`, `seg`, `blob`, `quad`, `tri`), 셰이더 `LIT`(물체), `SKY`, `WAT`(호수), `MW`(은하수).
3. **지형·소품 만들기**: `P`(정적 소품 메시)에 건물·벤치·철망·나무·돌탑·클로버밭·트램펄린 등을 쌓고, `B = {...}`로 GPU 버퍼를 만든다.
4. **사람 그리기**: `personRaw(m,x,y,z,h,ph,sw,shirt,o)`. 옵션 `o`: `sit`, `chair`, `lie`, `knees`, `ride`, `crouch`, `wave`, `eat`, `star`(점프 자세), `umb`, `torch`, `hat`, `longHair`, `pants`.
5. **동물**: 토끼·고라니(최대 고라니 2, 토끼 1), 고양이 '르샤'(직접 그린 모델). 여러 명이 접속하면 아이디가 가장 작은 사람(대표)이 동물을 움직이고 Firebase로 나눠 준다.
6. **축구공**: `stepBall`/`ballPhys`. 매일 아침 6시(한국 시각)에 센터서클로 돌아간다. 무늬 공은 `B.ball` + `ballRot` 회전.
7. **매 프레임 `frame()`**: 시간·날씨·이동·버튼 이름 정하기(`lab = ...` 줄)·그리기.
8. **Firebase 모듈**(파일 끝 `<script type="module">`): `window.MP`에 함께 걷기 기능을 붙인다.

### 시간과 날씨

- 하늘은 제천의 실제 시각(한국 시각)을 따른다. 날씨는 Open-Meteo에서 실시간으로 받는다.
- 시간대별 등장인물: 산책하는 남녀 06~23시, 손전등 순찰 23~06시, 테니스 18~23시, 반딧불 23~04시, 자정~00:30 맑은 날 은하수 보는 사람.
- 교육동 창문 불빛: 저녁에 켜지고 23~06시 꺼짐.

### 상호작용 (버튼 이름 → 함수)

| 버튼 | 조건 | 함수 |
|---|---|---|
| 벤치에 앉기 / 일어나기 | 벤치 근처 | `seated` |
| 고라니 타기 / 내리기 | 고라니 근처 | `mountDeer`, `dismount` |
| 토끼·르샤 쓰다듬기 | 근처 + 반응 중이 아닐 때(`animalBusy`) | `petRabbit`, `catReact`(르샤 반응 4가지 무작위) |
| 방울토마토 먹기 | 나무 근처 | `eatTomato` (열매는 90초 뒤 다시 열림, 모두 공유) |
| 네잎클로버 찾기 | 클로버밭 | `findClover` (5번에 1번 네잎) |
| 자전거 고치기 / 타기 / 내리기 | 자전거 근처 | `fixBike`(3번에 1번 성공), `mountBike`, `dismountBike`(내리면 다시 고장) |
| 기도하기 | 돌탑 근처 (다가가면 안내 문구) | `prayCairn` |
| 명언 뽑기 | 기계 앞 | `drawQuote` (`QUOTES` 배열, `'rare'` 표시는 황금 캡슐로 4배 드묾) |
| 방명록 보기 | 게시판 앞 | `openGB` |
| 점프 | 서 있을 때, 스페이스바도 됨 | `doJump` / `launch` |

**트램펄린:** 위에서 점프하면 1.1m, 착지 앞뒤 0.25초 안에 누르면 반동 ×1.45+0.25 (최대 `TRAMP_MAX` = 10m), 못 맞추면 반동 ×0.55. 점프 버튼 둘레 원(`#jg`)이 착지 타이밍을 보여 준다.

---

## 4. Firebase (함께 걷기·공유 데이터)

설정값(`cfg`)은 `index.html` 모듈 안에 있다. 웹 공개 설정이라 그대로 두어도 된다.

### 데이터 경로

| 경로 | 내용 |
|---|---|
| `players/{id}` | 접속자 위치·자세. 0.5초마다 바뀐 값만 보냄. 1분 넘게 화면을 안 보면 오프라인 처리 |
| `queue/{id}` | 동시 접속 20명 초과 시 대기열 (닉네임 '지니', '두더지'는 제한 없음) |
| `world/animals` | 동물 상태 (대표 접속자가 씀) |
| `world/ball` | 축구공 상태 |
| `world/acts/{key}` | 순간 사건들. `{동물id}`(쓰다듬기·타기), `tomato`(먹은 열매 f0~f27), `bike`(자전거 x,z,h,f=고쳐짐,r=탄 사람), `j{접속자id}`(점프 높이와 시각) |
| `stats/total`, `stats/monthly/YYYY-MM`, `stats/daily/YYYY-MM-DD`, `stats/hourly/YYYY-MM-DD/HH` | 방문 수 (들어서기 할 때마다 +1, 화면엔 안 보임) |
| `guestbook/{pushId}` | 방명록 `{n 이름, m 글, t 시각}` |
| `notices/{pushId}` | 관리자 공지 `{m, t}` |
| `admin/key` | 관리자 비밀번호 (문자열, 아무도 못 읽음) |
| `gbdel/{id}`, `nkey/{id}` | 관리자 삭제·공지 확인용 (읽기 금지) |

**중요:** 접속자 정보(`players/{id}`)에 새 항목을 넣으면 규칙에 막혀 위치 전송 전체가 실패할 수 있다. 새로 공유할 것이 있으면 `world/acts/{키}`(키 길이 12자 이하)를 쓰는 게 안전하다. 자전거·점프가 이 방식이다.

### 관리자 기능

- 방명록 창에서 '방명록' 제목을 3초 안에 5번 누르면 관리자 비밀번호 입력칸이 나온다.
- 비밀번호는 Firebase 콘솔 데이터에서 `admin/key`(문자열)로 정한다.
- 삭제는 `gbdel/{id}`에, 공지는 `nkey/{id}`에 비밀번호를 함께 써야 규칙이 허락한다.

### 규칙 (stats·guestbook·notices 부분)

```json
"stats": {
  ".read": false,
  "total": { ".write": true, ".validate": "newData.isNumber() && newData.val() == (data.exists() ? data.val() : 0) + 1" },
  "monthly": { "$m": { ".write": true, ".validate": "newData.isNumber() && newData.val() == (data.exists() ? data.val() : 0) + 1" } },
  "daily":   { "$d": { ".write": true, ".validate": "newData.isNumber() && newData.val() == (data.exists() ? data.val() : 0) + 1" } },
  "hourly":  { "$d": { "$h": { ".write": true, ".validate": "newData.isNumber() && newData.val() == (data.exists() ? data.val() : 0) + 1" } } }
},
"guestbook": {
  ".read": true,
  "$e": {
    ".write": "!data.exists() || (!newData.exists() && newData.parent().parent().child('gbdel').child($e).val() == root.child('admin').child('key').val())",
    ".validate": "newData.hasChildren(['n','m','t']) && newData.child('n').isString() && newData.child('n').val().length <= 10 && newData.child('m').isString() && newData.child('m').val().length >= 1 && newData.child('m').val().length <= 120 && newData.child('t').val() == now"
  }
},
"gbdel": { ".read": false, "$e": { ".write": "newData.val() == root.child('admin').child('key').val()" } },
"notices": {
  ".read": true,
  "$n": {
    ".write": "newData.parent().parent().child('nkey').child($n).val() == root.child('admin').child('key').val()",
    ".validate": "!newData.exists() || (newData.hasChildren(['m','t']) && newData.child('m').isString() && newData.child('m').val().length >= 1 && newData.child('m').val().length <= 200 && newData.child('t').val() == now)"
  }
},
"nkey": { ".read": false, "$n": { ".write": "newData.val() == root.child('admin').child('key').val()" } },
"admin": { ".read": false, ".write": false }
```

`players`, `world`, `queue` 규칙은 Firebase 콘솔의 현재 규칙을 그대로 둔다.

---

## 5. 테스트하는 법

```bash
# 저장소 루트에서
python3 -m http.server 8765 &
PAGE=index.html python3 tools/shot.py '[{"out":"a.png","w":400,"h":700,"wait":1500,
  "js":"sansa.weather(\"clear\");sansa.preview(-6);sansa.view(true);sansa.look(0,10,180,0.05)"}]'
```

- `tools/shot.py`는 Playwright + 크롬(swiftshader)으로 화면을 찍는다. 크롬 경로는 `/usr/bin/google-chrome`으로 되어 있으니 환경에 맞게 고친다.
- 헤드리스에서는 프레임이 느려서 게임 속 시간이 실제보다 느리게 흐른다. 애니메이션은 기다리는 시간을 넉넉히 둔다.
- 테스트 환경에서는 Firebase가 연결되지 않으므로, 함께 걷기 관련 동작은 실제 기기 두 대로 확인한다.

### 디버그 명령 `window.sansa`

| 명령 | 하는 일 |
|---|---|
| `look(x,z,방향도,고개)` | 카메라(내 위치)를 옮긴다. 방향 0 = 북, 90 = 동, 180 = 남 |
| `setHead(도)` | 캐릭터가 보는 방향 |
| `view(true/false)` | 3인칭 / 1인칭 |
| `preview(시간)` | 지금으로부터 몇 시간 뒤 하늘로 미리 보기 |
| `weather('clear'\|'rain'\|...)` | 날씨 바꾸기 |
| `deer()`, `rabbit()`, `animals()` | 동물 부르기, 목록 |
| `catGo()`, `catReact(k)`, `catH()` | 르샤 움직이기·반응·위치 |
| `ballSet(x,z,vx,vz)`, `ballPos()` | 축구공 |
| `tomato()`, `me()`, `H(x,z)`, `solids()` | 위치·지형 확인 |

---

## 6. Claude 아티팩트로 올릴 때

Claude 아티팩트는 `.glb` 파일을 따로 서비스하지 못하므로, 모델을 HTML 안에 넣은 파일을 만든다.

```bash
python3 tools/build_artifact.py   # -> artifact.html (약 8.7MB, 저장소에는 올리지 않음)
```

`index.html`의 `loadModel(...)`은 `<script id="bkdata|nddata|sddata">`에 든 base64가 있으면 그것을 쓰고, 없으면 같은 폴더의 `.glb` 파일을 불러온다.
이 `<script>`들은 반드시 `<body>` 바로 뒤에 들어가야 한다 (CSS 안에 들어가면 모델이 안 보인다).
(bkdata = bonkwan, nddata = saenghwal, sddata = namdong)

---

## 7. 지금까지 정한 것 (바꾸기 전에 참고)

- 이름은 **메타버스 청풍**. 시작 화면 문장: "바쁜 하루는 잠시 내려두고, 평안한 인재개발원에서 천천히 걸으며 쉬어 가세요."
- 옷 색은 파랑·노랑·자주·흰색 (녹색은 잔디와 헷갈려서 뺌).
- 고양이는 외부 3D 모델 대신 **직접 그린 르샤**를 쓴다 (외부 모델·자동 리깅은 결과가 나빠서 되돌림).
- 르샤는 걷기보다 앉아 있는 시간이 훨씬 길다 (멈출 때 20~50초).
- 다른 사람이 탄 고라니는 탄 사람 아래에 함께 그린다 (따로 그리면 늦게 따라오는 것처럼 보임).
- 축구공은 골이 들어가도 사라지지 않는다.
