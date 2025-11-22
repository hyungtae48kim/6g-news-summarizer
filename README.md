# 🌐 6G 뉴스 자동 요약 시스템

AI 기반 6G 기술 뉴스 자동 검색, 요약 및 전송 시스템

![React](https://img.shields.io/badge/React-18.2.0-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)

## ✨ 주요 기능

- 🔍 **실시간 검색**: Google News에서 최신 6G 기술 뉴스 자동 검색
- 🤖 **AI 자동 요약**: Google Gemini 2.5 Flash로 핵심 내용 분석 및 한국어 요약
- 📊 **Top 5 선정**: 가장 중요한 뉴스 5개 자동 선별
- 🔗 **원문 링크**: 각 뉴스의 출처로 바로 이동 가능
- 📧 **이메일 전송**: HTML 형식의 예쁜 뉴스레터 자동 발송
- 📱 **텔레그램 알림**: 실시간 푸시 알림으로 즉시 확인
- ⏰ **자동 스케줄링**: 매일 오전 9시(한국시간) 자동 실행
- 💰 **완전 무료**: 모든 서비스가 무료 (월 비용 $0)

---

## 🛠️ 기술 스택

### Frontend (Web App)
- **Framework**: React 18
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Build Tool**: Vite

### Backend (Automation)
- **Language**: Python 3.11
- **AI Model**: Google Gemini 2.5 Flash
- **Web Scraping**: BeautifulSoup4, Requests
- **Email**: SMTP (Gmail)
- **Messaging**: Telegram Bot API

### Infrastructure
- **CI/CD**: GitHub Actions
- **Scheduling**: Cron (Daily at 00:00 UTC / 09:00 KST)
- **Storage**: GitHub Artifacts (30일 보관)

---

## 📦 프로젝트 구조

```
6g-news-summarizer/
├── .github/
│   └── workflows/
│       └── daily-6g-news-gemini.yml    # GitHub Actions 워크플로우
├── src/
│   └── App.jsx                         # React 웹 애플리케이션
├── scripts/
│   └── fetch_and_email_gemini.py       # 뉴스 수집 및 전송 스크립트
├── output/                              # 생성된 뉴스 요약 파일
├── package.json                         # Node.js 의존성
├── README.md                            # 프로젝트 문서
└── .gitignore
```

---

## 🚀 빠른 시작

### 1️⃣ 저장소 복제

```bash
git clone https://github.com/your-username/6g-news-summarizer.git
cd 6g-news-summarizer
```

### 2️⃣ 필수 API 키 발급

#### Google Gemini API (무료)
1. [Google AI Studio](https://aistudio.google.com/) 접속
2. "Get API key" → "Create API key" 클릭
3. API 키 복사 (예: `AIzaSyC...`)

#### Gmail 앱 비밀번호
1. [Google 계정 관리](https://myaccount.google.com/) → 보안
2. 2단계 인증 활성화
3. 앱 비밀번호 생성 (메일, 기타 선택)
4. 16자리 비밀번호 복사

#### 텔레그램 봇 (선택사항)
1. 텔레그램에서 `@BotFather` 검색
2. `/newbot` 명령어로 봇 생성
3. Bot Token 복사
4. 봇에게 메시지 전송 후 `@userinfobot`으로 Chat ID 확인

### 3️⃣ GitHub Secrets 설정

Repository → Settings → Secrets and variables → Actions

**필수 Secrets (4개):**

| Secret 이름 | 설명 | 예시 |
|-------------|------|------|
| `GEMINI_API_KEY` | Google Gemini API 키 | `AIzaSyC...` |
| `GMAIL_USER` | 발신 Gmail 주소 | `your@gmail.com` |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 | `abcd efgh ijkl mnop` |
| `RECIPIENT_EMAIL` | 수신 이메일 주소 | `recipient@example.com` |

**선택 Secrets (텔레그램, 2개):**

| Secret 이름 | 설명 | 예시 |
|-------------|------|------|
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇 토큰 | `123456:ABCdef...` |
| `TELEGRAM_CHAT_ID` | 텔레그램 Chat ID | `987654321` |

### 4️⃣ 수동 실행 테스트

1. GitHub 저장소 → **Actions** 탭
2. **"Daily 6G News Summary (Gemini Free)"** 선택
3. **"Run workflow"** 버튼 클릭
4. 이메일/텔레그램 확인

---

## ⏰ 자동 스케줄

### 현재 설정
- **실행 시간**: 매일 오전 9시 (한국시간)
- **Cron 표현식**: `0 0 * * *` (UTC 00:00)

### 스케줄 변경 방법

`.github/workflows/daily-6g-news-gemini.yml` 파일 수정:

```yaml
schedule:
  # 매일 오후 6시 (한국시간)
  - cron: '0 9 * * *'
  
  # 주중만 (월-금)
  - cron: '0 0 * * 1-5'
  
  # 하루 2회 (오전 9시, 오후 6시)
  - cron: '0 0,9 * * *'
```

---

## 📧 이메일 샘플

<details>
<summary>이메일 미리보기</summary>

```
📡 6G 기술 뉴스 요약
생성일: 2025-11-22

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. China completes first phase of 6G technology trials
📅 November 2025

중국이 4년간의 6G 기술 시험 1단계를 완료하고 300개 이상의 
핵심 기술을 확보했습니다. 통신, 감지, 지능, 컴퓨팅 기술의 
통합 혁신을 달성했습니다.

💡 중요도: 글로벌 6G 기술 경쟁에서 중국의 리더십을 보여주는 
중요한 이정표입니다.

📰 출처: https://www.globaltimes.cn/...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[... Top 5 뉴스 계속 ...]
```

</details>

---

## 📱 텔레그램 알림 샘플

<details>
<summary>텔레그램 메시지 미리보기</summary>

```
📡 6G 기술 뉴스 요약
2025-11-22
━━━━━━━━━━━━━━

1. China completes first phase of 6G technology trials

중국이 4년간의 6G 기술 시험 1단계를 완료...

💡 글로벌 6G 기술 경쟁에서 중국의 리더십

🔗 원문 보기

━━━━━━━━━━━━━━

[... Top 5 뉴스 계속 ...]

🤖 GitHub Actions로 자동 생성됨
```

</details>

---

## 💰 비용 분석

### 월간 비용: **$0** (완전 무료)

| 서비스 | 무료 한도 | 사용량 | 비용 |
|--------|----------|--------|------|
| Google Gemini API | 1,500회/월 | 30회/월 | $0 |
| GitHub Actions | 2,000분/월 (Public) | ~30분/월 | $0 |
| Gmail SMTP | 500통/일 | 1통/일 | $0 |
| Telegram Bot API | 무제한 | 30회/월 | $0 |
| **총 비용** | - | - | **$0** |

---

## 🔧 개발 및 테스트

### 로컬 실행 (Python)

```bash
# 의존성 설치
pip install requests beautifulsoup4 lxml

# 환경 변수 설정
export GEMINI_API_KEY="your_key"
export GMAIL_USER="your@gmail.com"
export GMAIL_APP_PASSWORD="your_password"
export RECIPIENT_EMAIL="recipient@example.com"
export TELEGRAM_BOT_TOKEN="your_token"  # 선택
export TELEGRAM_CHAT_ID="your_chat_id"  # 선택

# 스크립트 실행
python scripts/fetch_and_email_gemini.py
```

### 로컬 실행 (React Web App)

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 브라우저에서 http://localhost:5173 열기
```

---

## 📊 기능 상세

### 1. 뉴스 검색
- **소스**: Google News RSS
- **키워드**: "6G technology 2025"
- **수집 개수**: 15개 뉴스
- **처리 시간**: ~2-3초

### 2. AI 요약
- **모델**: Google Gemini 2.5 Flash
- **입력**: 15개 뉴스 원문
- **출력**: Top 5 선정 + 한국어 요약
- **처리 시간**: ~5-8초

### 3. 전송
- **이메일**: HTML 포맷, 임베디드 스타일
- **텔레그램**: Markdown 포맷, 링크 버튼
- **저장**: GitHub Artifacts (txt 파일, 30일 보관)

---

## 🆘 문제 해결

### 1. GitHub Actions 실행 실패

**증상**: Workflow가 실행되지 않음

**해결:**
- Actions 탭에서 워크플로우 활성화 확인
- Repository Settings → Actions → Permissions 확인
- Secrets가 올바르게 설정되었는지 확인

### 2. Gemini API 404 오류

**증상**: `404 Client Error: Not Found`

**해결:**
- 모델명이 `gemini-2.5-flash`인지 확인 (gemini-1.5는 종료됨)
- API 키가 `AIza`로 시작하는지 확인
- [Google AI Studio](https://aistudio.google.com/)에서 키 재확인

### 3. 이메일 전송 실패

**증상**: `SMTPAuthenticationError`

**해결:**
- Gmail 2단계 인증 활성화 확인
- 앱 비밀번호가 16자리인지 확인
- `GMAIL_APP_PASSWORD`에 공백 포함 확인

### 4. 텔레그램 메시지 미수신

**증상**: 텔레그램 메시지가 안 옴

**해결:**
- Bot Token이 올바른지 확인
- Chat ID가 양수인지 확인 (개인 채팅)
- 봇에게 먼저 `/start` 메시지 전송 확인

---

## 🗺️ 로드맵

### 완료된 기능 ✅
- [x] 6G 뉴스 검색 및 AI 요약
- [x] 웹 애플리케이션 (React)
- [x] GitHub Actions 자동화
- [x] 이메일 전송
- [x] 텔레그램 알림
- [x] 완전 무료 구현

### 향후 계획 📋
- [ ] 여러 주제 지원 (AI, 양자컴퓨팅 등)
- [ ] 웹 대시보드 (히스토리 보기)
- [ ] Slack/Discord 연동
- [ ] 커스텀 키워드 설정
- [ ] 주간/월간 요약 리포트
- [ ] 다국어 지원

---

## 🤝 기여하기

기여를 환영합니다! 다음 방법으로 참여할 수 있습니다:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 👤 제작자

**Your Name**

- GitHub: [hyungtae48kim](https://github.com/hyungtae48kim)
- Email: lonelykht@gmail.com

---

## 🙏 감사의 말

- [Google Gemini](https://ai.google.dev/) - 무료 AI API 제공
- [Google News](https://news.google.com/) - 뉴스 소스
- [Telegram](https://telegram.org/) - 봇 API
- [GitHub Actions](https://github.com/features/actions) - 무료 CI/CD
- [Anthropic Claude](https://www.anthropic.com/) - 개발 지원

---

## 📞 문의 및 지원

프로젝트에 대한 질문이나 제안사항이 있으시면:

- 이슈 생성: [GitHub Issues](https://github.com/your-username/6g-news-summarizer/issues)
- 이메일: lonelykht@gmail.com

---

## 📸 스크린샷

### 웹 애플리케이션
<img src="docs/screenshot-web.png" alt="Web App" width="600">

### 이메일 뉴스레터
<img src="docs/screenshot-email.png" alt="Email" width="600">

### 텔레그램 알림
<img src="docs/screenshot-telegram.png" alt="Telegram" width="400">

---

⭐ 이 프로젝트가 유용하다면 Star를 눌러주세요!

**Made with ❤️ using Claude AI**