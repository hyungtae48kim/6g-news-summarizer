# 뉴스 날짜 필터링 기능 추가

## 변경 요약

뉴스 검색 시 **최근 7일 이내 기사만** 검색되도록 날짜 필터링 기능을 추가했습니다.

## 변경된 파일

### 1. `scripts/fetch_6g_professional.py`

#### `search_google_news()` 함수
- **변경 전**: 모든 기사 검색 (날짜 제한 없음)
- **변경 후**: 최근 7일 이내 기사만 검색
- **날짜 파싱**: RFC 2822 형식 (`Wed, 27 Dec 2025 10:30:00 GMT`)
- **사용 라이브러리**: `email.utils.parsedate_to_datetime()`

```python
def search_google_news(query, num_results=5, days=7):
    """Google 뉴스 검색 (News) - 최근 N일 이내 기사만 검색"""
    # 날짜 필터링 로직 추가
    cutoff_date = datetime.now() - timedelta(days=days)
    # 발행일이 cutoff_date 이전인 기사는 건너뛰기
```

#### `search_the_verge()` 함수
- **변경 전**: 모든 기사 검색 (날짜 제한 없음)
- **변경 후**: 최근 7일 이내 기사만 검색
- **날짜 파싱**: ISO 8601 형식 (`2025-12-27T10:30:00Z`)
- **사용 라이브러리**: `dateutil.parser.isoparse()`

```python
def search_the_verge(query, num_results=5, days=7):
    """The Verge Atom 피드 검색 (News) - 최근 N일 이내 기사만 검색"""
    # 날짜 필터링 로직 추가
    cutoff_date = datetime.now() - timedelta(days=days)
    # 발행일이 cutoff_date 이전인 기사는 건너뛰기
```

### 2. `requirements.txt`

새로운 의존성 추가:
```
python-dateutil>=2.8.2
```

**필요 이유**: The Verge의 ISO 8601 날짜 형식 파싱에 필요

### 3. `CLAUDE.md`

프로젝트 문서 업데이트:
- Data Sources 섹션에 날짜 필터링 정보 추가
- Key Implementation Details에 "News Date Filtering" 섹션 추가

### 4. `test_date_filtering.py` (신규)

날짜 필터링 기능 검증을 위한 테스트 스크립트:
- Google News 날짜 필터링 테스트
- The Verge 날짜 필터링 테스트
- 각 기사의 발행일 확인 및 검증

## 기능 세부사항

### 날짜 필터링 로직

1. **기준 날짜 계산**
   ```python
   cutoff_date = datetime.now() - timedelta(days=7)
   ```

2. **발행일 확인 및 비교**
   - 각 RSS/Atom 피드 아이템에서 `pubDate` 또는 `published` 태그 추출
   - 해당 날짜를 파싱하여 datetime 객체로 변환
   - cutoff_date와 비교하여 7일 이전 기사는 건너뛰기

3. **에러 처리**
   - 날짜 파싱 실패 시: Google News는 건너뛰기, The Verge는 포함 (보수적 접근)
   - 파싱 오류 메시지 출력: `⚠️ 날짜 파싱 오류: ...`

### 파라미터

두 함수 모두 `days` 파라미터 추가:
- **기본값**: `7` (1주일)
- **용도**: 검색 기간 조정 가능 (필요시 3일, 14일 등으로 변경 가능)

```python
# 최근 3일 이내 기사만 검색
search_google_news("6G", num_results=10, days=3)

# 최근 14일 이내 기사만 검색
search_the_verge("AI", num_results=10, days=14)
```

## 테스트 결과

### 실행 명령
```bash
source venv/bin/activate
python3 test_date_filtering.py
```

### 테스트 결과 (2025-12-27 실행)
```
Google News: 2개 기사 (최근 7일)
- LG유플러스, 6G 대비 '분산형 RIS' 실내 검증 성공 (1일 전) ✅
- "전원 없이 전파 제어"…LG유플러스, 6G 대비 실내 통신 기술 실증 (2일 전) ✅

The Verge: 10개 기사 (최근 7일)
- Trump's war on offshore wind faces another lawsuit (1일 전) ✅
- Rodeo is an app for making plans with friends (1일 전) ✅
- Framework announces another memory price hike (1일 전) ✅
- ... (총 10개 기사, 모두 7일 이내) ✅
```

**결과**: 모든 기사가 7일 이내로 올바르게 필터링됨 ✅

## 설치 방법

가상환경에서 새로운 의존성 설치:

```bash
source venv/bin/activate
pip install python-dateutil
```

또는 requirements.txt 재설치:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## 영향 범위

### 영향받는 부분
- ✅ Google News 검색 (최근 7일 이내만)
- ✅ The Verge 검색 (최근 7일 이내만)

### 영향받지 않는 부분
- ⚪ IEEE Xplore (학술 저널은 날짜 필터링 없음)
- ⚪ arXiv (연구 논문은 날짜 필터링 없음)

**이유**: 학술 논문과 저널은 최신성보다 관련성이 중요하므로 날짜 필터링 제외

## 주의사항

1. **날짜 파싱 오류**
   - RSS/Atom 피드의 날짜 형식이 표준을 따르지 않을 경우 파싱 오류 발생 가능
   - 오류 발생 시 콘솔에 경고 메시지 출력

2. **검색 결과 감소 가능**
   - 7일 이내 기사가 적을 경우 `num_results`보다 적은 결과 반환 가능
   - 예: `num_results=5` 요청했지만 7일 이내 기사가 2개뿐이면 2개만 반환

3. **시간대(Timezone) 처리**
   - 모든 날짜는 timezone-naive 비교 (UTC 기준)
   - 서버가 다른 시간대에 있어도 일관되게 작동

## 향후 개선 가능 사항

1. **날짜 필터링 설정 가능화**
   - 환경변수로 `NEWS_DAYS_FILTER` 추가 (예: 3, 7, 14, 30)
   - 기본값: 7일

2. **학술 자료 날짜 필터링**
   - IEEE Xplore, arXiv에도 선택적 날짜 필터링 적용 고려

3. **날짜 표시 개선**
   - 이메일/텔레그램 보고서에 "N일 전" 상대 날짜 표시

## 관련 이슈

- 요청: "뉴스 검색시 검색 시간 기준 1주일 이내 기사만 검색되도록 조치해줘"
- 구현일: 2025-12-27
- 구현자: Claude Code
