# 🌐 6G 뉴스 요약 프로그램

AI 기반 6G 기술 뉴스 검색 및 자동 요약 애플리케이션

![React](https://img.shields.io/badge/React-18.2.0-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)

## ✨ 주요 기능

- 🔍 **실시간 검색**: 최신 6G 기술 뉴스를 실시간으로 검색
- 🤖 **AI 자동 요약**: Claude AI가 핵심 내용을 자동으로 요약
- 📊 **Top 5 선정**: 가장 중요한 뉴스 5개를 자동 선별
- 🔗 **원문 링크**: 각 뉴스의 출처로 바로 이동
- 📋 **복사 기능**: 요약본을 클립보드에 쉽게 복사
- 💡 **중요도 분석**: 각 뉴스의 중요성과 의미 설명

## 🛠️ 기술 스택

- **Frontend**: React 18
- **AI**: Anthropic Claude Sonnet 4 API
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Build Tool**: Vite

## 📦 설치 방법

```bash
# 저장소 클론
git clone https://github.com/your-username/6g-news-summarizer.git

# 프로젝트 디렉토리로 이동
cd 6g-news-summarizer

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

## 🚀 사용 방법

1. 애플리케이션을 실행합니다
2. "최신 6G 뉴스 검색하기" 버튼을 클릭합니다
3. AI가 자동으로 최신 뉴스를 검색하고 요약합니다
4. 제목을 클릭하여 원문 기사를 확인할 수 있습니다
5. "요약본 복사하기" 버튼으로 내용을 복사할 수 있습니다

## 📸 스크린샷

### 메인 화면
- 깔끔한 UI/UX
- 그라디언트 디자인
- 반응형 레이아웃

### 검색 결과
- Top 5 뉴스 카드 형식
- 중요도 분석 포함
- 클릭 가능한 제목

## 🗺️ 로드맵

### Phase 1: 기본 기능 ✅
- [x] 6G 뉴스 검색
- [x] AI 자동 요약
- [x] Top 5 선정
- [x] 원문 링크 연결

### Phase 2: 자동화 (진행 예정)
- [ ] 매일 자동 실행 (Cron/스케줄러)
- [ ] Python 스크립트 통합
- [ ] GitHub Actions 자동화

### Phase 3: 알림 기능 (계획)
- [ ] 카카오톡 API 연동
- [ ] 이메일 전송 기능
- [ ] Slack/Discord 웹훅

## 📂 프로젝트 구조

```
6g-news-summarizer/
├── src/
│   ├── App.jsx          # 메인 React 컴포넌트
│   └── main.jsx         # 진입점
├── public/
├── package.json         # 프로젝트 설정
├── vite.config.js       # Vite 설정
├── tailwind.config.js   # Tailwind 설정
├── README.md            # 프로젝트 문서
└── .gitignore           # Git 제외 파일
```

## 🔧 환경 변수

현재 버전에서는 별도의 API 키 설정이 필요하지 않습니다.
향후 카카오톡 연동 시 `.env` 파일이 필요합니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 👤 제작자

**hyungtae48kim**

- GitHub: [@your-username](https://github.com/hyungtae48kim)

## 🙏 감사의 말

- [Anthropic](https://www.anthropic.com/) - Claude AI API 제공
- [Lucide](https://lucide.dev/) - 아이콘 제공
- [Tailwind CSS](https://tailwindcss.com/) - 스타일링 프레임워크

## 📞 문의

프로젝트에 대한 질문이나 제안사항이 있으시면 이슈를 생성해주세요!

---

⭐ 이 프로젝트가 유용하다면 Star를 눌러주세요!
