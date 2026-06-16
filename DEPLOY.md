# PCCS2 클라우드 배포 (Fly.io)

집 컴퓨터를 켜두지 않아도, **외부 데이터망에서 핸드폰만으로 항상** 접속할 수 있게
PCCS2를 Fly.io에 올리는 방법입니다. 한 번만 설정해두면 됩니다.

배포되는 것:
- **백엔드** (FastAPI) — `pccs2-backend` 앱
- **프론트엔드** (Next.js) — `pccs2-web` 앱
- **PostgreSQL** — Fly에서 제공 (로컬 SQLite 대신 클라우드 DB 사용)

> **RDP-DB 동기화는?** 클라우드 서버는 집 컴퓨터의 `rdp.db` 파일을 직접 읽지
> 못합니다. 그래서 클라우드에서는 **앱의 "RDP-DB 가져오기 → 파일 업로드"** 화면에서
> `rdp.db`를 가끔 올려 동기화합니다. (자세한 내용은 맨 아래 참고)

---

## 0. 준비 (한 번만)

1. Fly.io 계정 만들기: https://fly.io/app/sign-up (결제카드 등록 필요 — 소규모는 사실상 무료~월 몇 달러)
2. Fly CLI 설치:
   - macOS: `brew install flyctl`
   - 그 외: https://fly.io/docs/flyctl/install/
3. 로그인:
   ```bash
   fly auth login
   ```

이 저장소 루트(`fly.backend.toml`이 있는 폴더)에서 아래 명령들을 실행합니다.

---

## 1. 앱 2개 만들기 (배포는 아직 안 함)

```bash
fly apps create pccs2-backend
fly apps create pccs2-web
```

> 다른 이름을 쓰고 싶으면 `fly.backend.toml`·`fly.frontend.toml`의 `app =` 값과
> 아래 모든 명령의 이름을 같이 바꿔야 합니다. 처음엔 그냥 이 이름을 권장합니다.

---

## 2. PostgreSQL 만들고 백엔드에 연결

```bash
# DB 클러스터 생성 (이름·리전은 기본값 권장, 가장 작은 사양 선택)
fly postgres create --name pccs2-db --region nrt

# 백엔드 앱에 연결 → DATABASE_URL 시크릿이 자동으로 설정됨
fly postgres attach pccs2-db --app pccs2-backend
```

> Fly가 "Managed Postgres(MPG)를 쓰라"고 안내할 수 있습니다. 안내대로 `fly mpg`
> 명령을 써도 되며, 결과(=백엔드에 `DATABASE_URL`이 설정되는 것)는 같습니다.
> 코드는 `postgres://` 주소를 자동으로 비동기 드라이버로 변환하므로 별도 수정이 필요 없습니다.

---

## 3. 백엔드 시크릿 설정 후 배포

```bash
# 프론트엔드 주소에서 오는 요청을 허용(CORS)하고, 세션 키를 설정
fly secrets set \
  CORS_ORIGINS="https://pccs2-web.fly.dev" \
  SECRET_KEY="$(openssl rand -hex 32)" \
  --app pccs2-backend

# 배포
fly deploy -c fly.backend.toml
```

확인:
```bash
curl https://pccs2-backend.fly.dev/api/predict/health
# {"status":"healthy_untrained", ...} 가 나오면 성공
```

---

## 4. 프론트엔드 배포

`fly.frontend.toml`에 백엔드 주소(`https://pccs2-backend.fly.dev`)가 이미 들어 있습니다.
백엔드 이름을 바꿨다면 그 파일의 `NEXT_PUBLIC_API_URL`도 바꾸세요.

```bash
fly deploy -c fly.frontend.toml
```

배포가 끝나면 접속 주소:
```
https://pccs2-web.fly.dev
```

---

## 5. 핸드폰에서 사용 + 앱처럼 설치

1. 핸드폰 브라우저에서 `https://pccs2-web.fly.dev` 접속 (데이터망/어디서든 OK)
2. 홈 화면에 설치 (PWA):
   - 아이폰 Safari: 공유 → "홈 화면에 추가"
   - 안드로이드 Chrome: 메뉴(⋮) → "홈 화면에 추가"

HTTPS로 제공되므로 PWA 설치가 정상 동작합니다.

---

## 6. RDP-DB 동기화 (가끔 업로드)

클라우드 서버는 집 컴퓨터의 파일을 못 읽으므로 **업로드 방식**으로 동기화합니다.

1. 앱에서 **RDP-DB 가져오기** 화면으로 이동
2. **"파일 업로드"** 영역에서 본인 `rdp.db` 선택 → **"업로드로 가져오기"**
3. 이미 가져온 배합은 자동으로 건너뛰고, 바뀐 행만 업데이트됩니다 (반복 실행 안전)

> "자동 가져오기(권장)" 영역은 *로컬 실행*용입니다. 클라우드에서는 파일을 찾지 못했다고
> 표시되는 게 정상이며, 아래 "파일 업로드"를 사용하면 됩니다.
>
> 반대로 PCCS2에서 수정한 내용을 다시 `rdp.db`로 되돌리는 기능(`sync-back`, 엑셀 export)은
> 서버의 로컬 파일을 전제로 하므로 클라우드에서는 동작하지 않습니다. 그 작업은 집
> 컴퓨터에서 `./start.sh`(로컬 실행)로 하면 됩니다.

---

## 비용 절약 / 항상 켜두기

- 기본 설정은 **요청이 없으면 머신을 잠재웠다가** 접속 시 깨웁니다(첫 접속이 수 초 느림).
  비용이 거의 들지 않습니다.
- 항상 즉시 응답하게 하려면 `fly.backend.toml`·`fly.frontend.toml`의
  `min_machines_running = 0` 을 `1` 로 바꾸고 다시 `fly deploy` 하세요. (소액 과금)

## 업데이트 배포

코드를 고친 뒤 다시 올리려면:
```bash
fly deploy -c fly.backend.toml     # 백엔드 변경 시
fly deploy -c fly.frontend.toml    # 프론트엔드 변경 시
```

## 로그 / 상태 확인

```bash
fly logs --app pccs2-backend
fly status --app pccs2-backend
```
