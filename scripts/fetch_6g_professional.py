#!/usr/bin/env python3
"""
6G 기술 전문 검색 및 요약 시스템 (RAN Network Professor & RAN SW Engineer Persona)
- 매일 동적으로 6G hot keywords 추출
- 각 소스에서 10개씩 총 30개 아이템 수집 (IEEE, arXiv, Google News)
- RAN SW 개발자 관점에서 10개 선별
- 선별된 아이템에 대해 심층 요약

Note: Google Scholar removed due to bot detection (HTTP 429 + CAPTCHA)
"""

import os
import json
import smtplib
import requests
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from bs4 import BeautifulSoup

# ==================== 유틸리티 함수 ====================

def clean_json_string(text):
    """JSON 문자열에서 문제가 될 수 있는 특수문자 정제"""
    # 백슬래시와 따옴표 문제 해결
    # 이미 이스케이프된 백슬래시 보호
    text = text.replace('\\\\', '\x00')  # 임시 마커
    # 이스케이프되지 않은 백슬래시 제거
    text = text.replace('\\', '')
    # 임시 마커 복원
    text = text.replace('\x00', '\\\\')

    return text

def extract_json_from_text(text):
    """텍스트에서 JSON 객체/배열 추출"""
    # 마크다운 코드블록 제거
    text = re.sub(r'```(?:json|python)?\s*', '', text)
    text = text.replace('```', '')

    # JSON 배열 찾기 [...]
    array_match = re.search(r'\[[\s\S]*\]', text)
    if array_match:
        return array_match.group(0).strip()

    # JSON 객체 찾기 {...}
    obj_match = re.search(r'\{[\s\S]*\}', text)
    if obj_match:
        return obj_match.group(0).strip()

    return text.strip()

# ==================== Hot Keyword 추출 ====================

def extract_hot_keywords():
    """Gemini를 사용하여 오늘의 6G hot keywords 추출"""

    api_key = os.environ.get('GEMINI_API_KEY')

    if not api_key:
        print("⚠️ GEMINI_API_KEY 없음. 기본 키워드 사용.")
        return "6G wireless communications"

    prompt = f"""You are a RAN Network professor and expert in 6G technology trends.

Today's date: {datetime.now().strftime('%Y-%m-%d')}

Based on the latest 6G technology trends in {datetime.now().year}, suggest ONE focused search query (3-5 words) that would be most relevant for RAN SW engineers this week.

Consider these areas:
- RAN architecture and protocols
- O-RAN and Open RAN developments
- 6G PHY layer innovations
- AI/ML in RAN
- Network slicing
- Terahertz communications
- Reconfigurable intelligent surfaces (RIS)
- Digital twin for networks
- The latest 6G technology trends

Return ONLY the search query phrase in English, nothing else. No explanation, no quotes.

Example outputs:
- 6G RAN AI optimization
- Open RAN intelligent controller
- 6G terahertz beamforming
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096,  # Gemini 2.5 uses ~2000 tokens for thinking, need extra for actual output
        }
    }

    try:
        print("🔍 Gemini로 오늘의 Hot Keyword 추출 중...")
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=30)

        # 429 Rate Limit 처리
        if response.status_code == 429:
            print("⚠️ Rate limit 도달. 5초 대기 후 재시도...")
            import time
            time.sleep(5)
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=30)

        response.raise_for_status()

        data = response.json()

        # 디버깅: API 응답 구조 확인
        print(f"📝 Gemini API 응답 키: {list(data.keys())}")

        if 'candidates' in data and len(data['candidates']) > 0:
            candidate = data['candidates'][0]

            # 디버깅: candidate 구조 확인
            print(f"📝 Candidate 키: {list(candidate.keys())}")

            # finishReason 확인
            finish_reason = candidate.get('finishReason', 'UNKNOWN')
            if finish_reason == 'MAX_TOKENS':
                print(f"⚠️ MAX_TOKENS에 도달. maxOutputTokens를 늘려야 합니다.")

            if 'content' in candidate:
                content = candidate['content']
                if 'parts' in content and len(content['parts']) > 0:
                    keyword = content['parts'][0].get('text', '').strip()
                    keyword = keyword.replace('"', '').replace("'", "").strip()

                    if keyword:
                        print(f"✅ Hot Keyword: '{keyword}'")
                        return keyword
                    else:
                        print("⚠️ 키워드가 비어있음.")
                else:
                    print(f"⚠️ parts 없음. Content: {content}")
            else:
                print(f"⚠️ content 없음. Candidate: {candidate}")

        print("⚠️ 키워드 추출 실패. 기본 키워드 사용.")
        print(f"📝 전체 응답: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
        return "6G wireless communications"

    except Exception as e:
        print(f"❌ 키워드 추출 오류: {e}")
        import traceback
        traceback.print_exc()
        return "6G wireless communications"

# ==================== 검색 함수 ====================

def search_google_scholar(query, num_results=5):
    """Google Scholar에서 6G 논문 검색 (Papers)"""
    
    print(f"📚 Google Scholar 검색 중: {query}")
    
    # Google Scholar RSS/API 대안으로 일반 검색 사용
    search_url = f"https://scholar.google.com/scholar?q={query}&hl=en&as_sdt=0,5"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = []
        papers = soup.find_all('div', class_='gs_ri', limit=num_results)
        
        for paper in papers:
            title_elem = paper.find('h3', class_='gs_rt')
            snippet_elem = paper.find('div', class_='gs_rs')
            
            if title_elem:
                # 제목에서 링크 추출
                link_elem = title_elem.find('a')
                title = title_elem.get_text()
                url = link_elem['href'] if link_elem and link_elem.has_attr('href') else ''
                
                # 초록 추출
                snippet = snippet_elem.get_text() if snippet_elem else ''
                
                results.append({
                    'title': title.strip(),
                    'description': snippet.strip(),
                    'url': url,
                    'type': 'Paper'
                })
        
        print(f"✅ {len(results)}개 논문 발견")
        return results
        
    except Exception as e:
        print(f"❌ Google Scholar 검색 오류: {e}")
        return []

def search_arxiv(query, num_results=5):
    """arXiv에서 6G 논문 검색 (Papers)"""
    
    print(f"📄 arXiv 검색 중: {query}")
    
    url = "http://export.arxiv.org/api/query"
    params = {
        'search_query': f'all:{query}',
        'start': 0,
        'max_results': num_results,
        'sortBy': 'relevance',
        'sortOrder': 'descending'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        soup = BeautifulSoup(response.content, 'xml')
        
        results = []
        entries = soup.find_all('entry')
        
        for entry in entries:
            title = entry.find('title').get_text().strip()
            summary = entry.find('summary').get_text().strip()
            link = entry.find('id').get_text().strip()
            
            results.append({
                'title': title,
                'description': summary[:300],
                'url': link,
                'type': 'Paper'
            })
        
        print(f"✅ {len(results)}개 논문 발견")
        return results
        
    except Exception as e:
        print(f"❌ arXiv 검색 오류: {e}")
        return []

def search_ieee(query, num_results=5, api_key=None):
    """IEEE Xplore API를 사용한 검색 (Journals)"""

    print(f"📰 IEEE Xplore 검색 중: {query}")

    # API 키 확인 (환경변수 또는 파라미터)
    if api_key is None:
        api_key = os.environ.get('IEEE_API_KEY')

    if not api_key:
        print("⚠️ IEEE API 키가 설정되지 않았습니다. IEEE_API_KEY 환경변수를 설정하세요.")
        print("   API 키 발급: https://developer.ieee.org/")
        return []

    # IEEE Xplore API 엔드포인트
    api_url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"

    params = {
        'apikey': api_key,
        'querytext': query,
        'max_records': num_results,
        'sort_order': 'desc',
        'sort_field': 'publication_year'
    }

    try:
        response = requests.get(api_url, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()

        results = []
        articles = data.get('articles', [])

        for article in articles:
            title = article.get('title', 'No title')
            abstract = article.get('abstract', 'No abstract available')
            article_number = article.get('article_number', '')
            publication_title = article.get('publication_title', '')

            # 설명 생성 (abstract 앞부분 + 저널명)
            description = abstract[:200] + '...' if len(abstract) > 200 else abstract
            if publication_title:
                description = f"[{publication_title}] {description}"

            results.append({
                'title': title,
                'description': description,
                'url': f"https://ieeexplore.ieee.org/document/{article_number}",
                'type': 'Journal'
            })

        print(f"✅ {len(results)}개 저널 발견")
        return results

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print(f"❌ IEEE API 인증 오류: API 키를 확인하세요.")
        else:
            print(f"❌ IEEE API HTTP 오류: {e}")
        return []
    except Exception as e:
        print(f"❌ IEEE 검색 오류: {e}")
        return []

def search_google_news(query, num_results=5):
    """Google 뉴스 검색 (News)"""
    
    print(f"📰 구글 뉴스 검색 중: {query}")
    
    url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item', limit=num_results)
        
        results = []
        for item in items:
            # Google News RSS uses redirect URLs - extract the actual URL
            redirect_url = item.link.text if item.link else ''
            actual_url = redirect_url

            # Try to resolve the redirect to get the actual article URL
            if redirect_url:
                try:
                    # Follow redirects to get the final URL
                    head_response = requests.head(redirect_url, allow_redirects=True, timeout=5)
                    actual_url = head_response.url
                except:
                    # If redirect fails, keep the original URL
                    actual_url = redirect_url

            results.append({
                'title': item.title.text if item.title else '',
                'description': item.description.text if item.description else '',
                'url': actual_url,
                'pub_date': item.pubDate.text if item.pubDate else '',
                'type': 'News'
            })
        
        print(f"✅ {len(results)}개 뉴스 발견")
        return results
        
    except Exception as e:
        print(f"❌ Google News 검색 오류: {e}")
        return []

# ==================== AI 아이템 선별 함수 ====================

def select_top_items_for_ran_engineers(all_items, top_n=10):
    """Gemini를 사용하여 RAN SW 개발자에게 가장 유용한 아이템 선별"""

    api_key = os.environ.get('GEMINI_API_KEY')

    if not api_key:
        print("⚠️ GEMINI_API_KEY 없음. 상위 10개 아이템만 사용.")
        return all_items[:top_n]

    # 아이템 정보 구성 (특수문자 완전 제거)
    items_context = ""
    for i, item in enumerate(all_items, 1):
        # 특수문자 완전 제거 (백슬래시 이스케이프 대신)
        title = item['title'].replace('"', '').replace("'", '').replace('\\', '').replace('\n', ' ').replace('\r', ' ').strip()[:150]
        description = item['description'].replace('"', '').replace("'", '').replace('\\', '').replace('\n', ' ').replace('\r', ' ').strip()[:200]

        items_context += f"\n{i}. [{item['type']}] {title}\n"
        items_context += f"   Description: {description}\n"

    prompt = f"""You are a RAN Network Professor and RAN SW Engineer expert.

Given {len(all_items)} items below (Journals, Papers, News), select exactly {top_n} items that would provide the MOST valuable insights for RAN SW developers.

Selection criteria:
- Practical applicability to RAN software development
- Novel algorithms or architectures relevant to RAN
- O-RAN and Open RAN developments
- AI/ML applications in RAN optimization
- PHY layer innovations affecting upper layers
- Real-world deployment experiences
- Performance optimization techniques

Items:
{items_context}

IMPORTANT: Return ONLY a valid JSON array of selected item numbers (1-indexed).
- No markdown code blocks
- No explanations
- Just the plain JSON array

Example output format:
[1, 5, 7, 12, 15, 18, 23, 28, 35, 40]
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 8192,  # Gemini 2.5 uses ~3000-4000 tokens for thinking on complex tasks
        }
    }

    try:
        print(f"🤖 Gemini로 RAN SW 개발자용 Top {top_n} 아이템 선별 중...")

        # Rate limit 방지 대기
        import time
        time.sleep(2)

        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)

        # 429 Rate Limit 및 500 Server Error 처리
        if response.status_code == 429:
            print("⚠️ Rate limit 도달. 10초 대기 후 재시도...")
            time.sleep(10)
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)
        elif response.status_code == 500:
            print("⚠️ 서버 오류. 5초 대기 후 재시도...")
            time.sleep(5)
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)

        response.raise_for_status()

        data = response.json()

        if 'candidates' in data and len(data['candidates']) > 0:
            candidate = data['candidates'][0]

            # finishReason 확인
            finish_reason = candidate.get('finishReason', 'UNKNOWN')
            if finish_reason == 'MAX_TOKENS':
                print(f"⚠️ MAX_TOKENS에 도달. maxOutputTokens를 늘려야 합니다.")

            if 'content' in candidate and 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                text = candidate['content']['parts'][0].get('text', '').strip()

                # JSON 추출 및 정제
                json_text = extract_json_from_text(text)
                clean_text = clean_json_string(json_text)

                # 응답 디버깅
                print(f"📝 Gemini 응답 (처음 300자): {clean_text[:300]}")

                try:
                    selected_indices = json.loads(clean_text)

                    # 배열인지 확인
                    if not isinstance(selected_indices, list):
                        print(f"⚠️ 응답이 배열이 아님: {type(selected_indices)}")
                        print(f"📝 응답 내용: {selected_indices}")
                        return all_items[:top_n]

                    # 선별된 아이템만 추출 (1-indexed를 0-indexed로 변환)
                    selected_items = []
                    for idx in selected_indices:
                        if isinstance(idx, int) and 1 <= idx <= len(all_items):
                            selected_items.append(all_items[idx - 1])
                        else:
                            print(f"⚠️ 잘못된 인덱스 무시: {idx}")

                    if len(selected_items) >= top_n:
                        print(f"✅ {len(selected_items)}개 아이템 선별 완료")
                        return selected_items[:top_n]
                    else:
                        print(f"⚠️ 선별된 아이템 부족 ({len(selected_items)}개). 상위 {top_n}개 사용.")
                        return all_items[:top_n]

                except json.JSONDecodeError as e:
                    print(f"❌ JSON 파싱 오류: {e}")
                    print(f"❌ 오류 위치: line {e.lineno}, column {e.colno}")
                    print(f"❌ 응답 전체:\n{clean_text[:500]}")

                    # 디버깅 파일 저장
                    debug_file = f"debug_selection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(f"원본 텍스트:\n{text}\n\n")
                        f.write(f"JSON 추출:\n{json_text}\n\n")
                        f.write(f"정제 후:\n{clean_text}\n")
                    print(f"💾 전체 응답이 {debug_file}에 저장되었습니다.")

                    return all_items[:top_n]
            else:
                print(f"⚠️ content 또는 parts 없음. Candidate: {candidate}")

        print("⚠️ 아이템 선별 실패. 상위 10개 사용.")
        return all_items[:top_n]

    except Exception as e:
        print(f"❌ 아이템 선별 오류: {e}")
        import traceback
        traceback.print_exc()
        return all_items[:top_n]

# ==================== AI 요약 함수 ====================

def summarize_with_gemini(items):
    """Gemini AI로 6G 엔지니어 관점 요약"""
    
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key:
        print("⚠️ GEMINI_API_KEY 없음. AI 요약 생략.")
        return create_summary_without_ai(items)
    
    # 아이템 정보 구성 (특수문자 완전 제거 - 이스케이프 문제 방지)
    items_context = ""
    for i, item in enumerate(items, 1):
        # 특수문자 완전 제거 (JSON 파싱 오류 방지)
        title = item['title'].replace('"', '').replace("'", '').replace('\\', '').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()[:200]
        description = item['description'].replace('"', '').replace("'", '').replace('\\', '').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()[:300]
        url = item['url'].replace('"', '').replace('\\', '').strip()

        items_context += f"\n{i}. [{item['type']}] {title}\n"
        items_context += f"Description: {description}\n"
        items_context += f"Link: {url}\n"
    
    prompt = f"""당신은 RAN Network Professor이자 RAN SW 개발 엔지니어입니다.

다음 선별된 6G/RAN 관련 자료들을 RAN SW 개발자 관점에서 분석하고 요약해주세요.

자료 목록:
{items_context}

각 자료에 대해 다음 형식으로 요약하세요. 반드시 유효한 JSON 형식만 반환하고 다른 텍스트는 포함하지 마세요:

IMPORTANT:
- JSON 문자열 내부의 모든 특수문자는 반드시 이스케이프하세요 (따옴표, 백슬래시 등)
- 줄바꿈은 공백으로 대체하세요
- 문자열을 중간에 끊지 마세요
- 유효한 JSON만 반환하세요

{{
  "summaries": [
    {{
      "title": "논문 또는 저널 또는 뉴스 제목",
      "summary": "핵심 내용을 3-4문장으로 요약 (한국어). RAN 아키텍처, 알고리즘, 프로토콜 관점 포함.",
      "message": "RAN SW 개발자에게 주는 실무적 시사점과 적용 가능성 (한국어). 구체적인 SW 구현 관점 제시.",
      "url": "원문 링크",
      "type": "Journal 또는 Paper 또는 News"
    }}
  ],
  "generatedAt": "{datetime.now().strftime('%Y-%m-%d')}"
}}

RAN SW 개발 관점에서 다음을 중점적으로 분석하세요:
- RAN 프로토콜 스택 (MAC/RLC/PDCP/RRC) 영향
- O-RAN/Open RAN 인터페이스 및 아키텍처
- AI/ML 기반 RAN 최적화 알고리즘
- 실시간 성능 요구사항 및 최적화 기법
- 실제 구현 시 고려사항"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 16384,  # High limit for complex summarization (thinking + long output)
        }
    }
    
    try:
        print("🤖 Gemini AI로 요약 중...")

        # Rate limit 방지 대기
        import time
        time.sleep(2)

        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)

        # 429 Rate Limit 및 500 Server Error 처리
        if response.status_code == 429:
            print("⚠️ Rate limit 도달. 10초 대기 후 재시도...")
            time.sleep(10)
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)
        elif response.status_code == 500:
            print("⚠️ 서버 오류. 5초 대기 후 재시도...")
            time.sleep(5)
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)

        response.raise_for_status()
        
        data = response.json()
        
        if 'candidates' in data and len(data['candidates']) > 0:
            candidate = data['candidates'][0]

            # finishReason 확인
            finish_reason = candidate.get('finishReason', 'UNKNOWN')
            print(f"📝 finishReason: {finish_reason}")
            if finish_reason == 'MAX_TOKENS':
                print(f"⚠️ MAX_TOKENS에 도달. 응답이 불완전할 수 있습니다.")

            if 'content' in candidate and 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                text = candidate['content']['parts'][0].get('text', '')

                # JSON 추출 및 정제
                json_text = extract_json_from_text(text)
                clean_text = clean_json_string(json_text)

                # 파싱 전 디버깅
                print(f"응답 텍스트 길이: {len(clean_text)}")
                print(f"응답 시작 (200자): {clean_text[:200]}")

                try:
                    results = json.loads(clean_text)

                    # 결과 검증 및 정규화
                    if isinstance(results, list):
                        # 배열로 반환된 경우 (summaries만 반환)
                        print(f"📝 배열 형식 응답 감지. 객체로 변환 중...")
                        normalized_results = {
                            "summaries": results,
                            "generatedAt": datetime.now().strftime('%Y-%m-%d')
                        }
                        print(f"✅ {len(normalized_results['summaries'])}개 요약 완료")
                        return normalized_results
                    elif isinstance(results, dict):
                        if 'summaries' not in results:
                            print(f"⚠️ 'summaries' 키 없음. 응답 키: {list(results.keys())}")
                            return create_summary_without_ai(items)
                        print(f"✅ {len(results['summaries'])}개 요약 완료")
                        return results
                    else:
                        print(f"⚠️ 잘못된 응답 타입: {type(results)}")
                        return create_summary_without_ai(items)

                except json.JSONDecodeError as e:
                    print(f"❌ JSON 파싱 오류: {e}")
                    print(f"오류 위치: line {e.lineno}, column {e.colno}")

                    # 문제 영역 출력 (오류 위치 전후 200자)
                    error_pos = e.pos if hasattr(e, 'pos') else 0
                    start_pos = max(0, error_pos - 200)
                    end_pos = min(len(clean_text), error_pos + 200)
                    print(f"문제 영역:\n{clean_text[start_pos:end_pos]}")
                    print(f"\n전체 응답 저장 중...")

                    # 디버깅을 위해 전체 응답을 파일로 저장
                    debug_file = f"debug_gemini_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(f"원본:\n{text}\n\n")
                        f.write(f"JSON 추출:\n{json_text}\n\n")
                        f.write(f"정제 후:\n{clean_text}\n")
                    print(f"전체 응답이 {debug_file}에 저장되었습니다.")

                    return create_summary_without_ai(items)
        
        print("⚠️ AI 요약 실패. 기본 요약 사용.")
        return create_summary_without_ai(items)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Gemini API 오류: {e}")
        return create_summary_without_ai(items)
    except Exception as e:
        print(f"❌ Gemini API 오류: {e}")
        return create_summary_without_ai(items)

def create_summary_without_ai(items):
    """AI 없이 기본 요약 생성"""
    
    results = {
        "summaries": [],
        "generatedAt": datetime.now().strftime('%Y-%m-%d')
    }
    
    for item in items:
        results["summaries"].append({
            "title": item['title'],
            "summary": item['description'][:300] if item.get('description') else "내용을 확인하세요.",
            "message": f"6G 기술 발전의 최신 동향을 보여주는 {item['type']} 자료입니다.",
            "url": item['url'],
            "type": item['type']
        })
    
    return results

# ==================== 이메일 전송 ====================

def create_html_email(summary_data):
    """HTML 이메일 생성 (Engineer 포맷)"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background-color: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
            }}
            .header .subtitle {{
                color: #e0e0e0;
                font-size: 14px;
                margin-top: 10px;
            }}
            .section {{
                margin-bottom: 40px;
            }}
            .section-title {{
                color: #1e3a8a;
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 3px solid #3b82f6;
            }}
            .item {{
                background-color: #f9fafb;
                border-left: 4px solid #3b82f6;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 5px;
            }}
            .item-type {{
                display: inline-block;
                background: #3b82f6;
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .item-title {{
                color: #1e3a8a;
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 15px;
            }}
            .item-title a {{
                color: #1e3a8a;
                text-decoration: none;
            }}
            .item-title a:hover {{
                text-decoration: underline;
            }}
            .summary {{
                color: #4b5563;
                margin-bottom: 15px;
                line-height: 1.8;
            }}
            .message {{
                background-color: #eff6ff;
                border-left: 3px solid #2563eb;
                padding: 15px;
                margin-top: 15px;
                border-radius: 3px;
            }}
            .message-label {{
                color: #1e40af;
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 8px;
            }}
            .message-text {{
                color: #1e40af;
                font-size: 14px;
            }}
            .source {{
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid #e5e7eb;
            }}
            .source a {{
                color: #2563eb;
                text-decoration: none;
                font-size: 14px;
            }}
            .source a:hover {{
                text-decoration: underline;
            }}
            .footer {{
                text-align: center;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                color: #999;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔬 6G Technology Intelligence Report</h1>
                <div class="subtitle">Engineer's Perspective | {summary_data['generatedAt']}</div>
            </div>
    """
    
    # Journal, Paper, News별로 그룹핑
    groups = {'Journal': [], 'Paper': [], 'News': []}
    for item in summary_data['summaries']:
        item_type = item.get('type', 'News')
        groups[item_type].append(item)
    
    # Journal 섹션
    if groups['Journal']:
        html += '<div class="section"><div class="section-title">📚 Academic Journals</div>'
        for item in groups['Journal']:
            html += f"""
            <div class="item">
                <span class="item-type">JOURNAL</span>
                <div class="item-title">
                    <a href="{item['url']}" target="_blank">{item['title']}</a>
                </div>
                <div class="summary">{item['summary']}</div>
                <div class="message">
                    <div class="message-label">💡 Engineer's Insight</div>
                    <div class="message-text">{item['message']}</div>
                </div>
                <div class="source">
                    🔗 <a href="{item['url']}" target="_blank">Read Full Article</a>
                </div>
            </div>
            """
        html += '</div>'
    
    # Paper 섹션
    if groups['Paper']:
        html += '<div class="section"><div class="section-title">📄 Research Papers</div>'
        for item in groups['Paper']:
            html += f"""
            <div class="item">
                <span class="item-type">PAPER</span>
                <div class="item-title">
                    <a href="{item['url']}" target="_blank">{item['title']}</a>
                </div>
                <div class="summary">{item['summary']}</div>
                <div class="message">
                    <div class="message-label">💡 Engineer's Insight</div>
                    <div class="message-text">{item['message']}</div>
                </div>
                <div class="source">
                    🔗 <a href="{item['url']}" target="_blank">Read Full Paper</a>
                </div>
            </div>
            """
        html += '</div>'
    
    # News 섹션
    if groups['News']:
        html += '<div class="section"><div class="section-title">📰 Industry News</div>'
        for item in groups['News']:
            html += f"""
            <div class="item">
                <span class="item-type">NEWS</span>
                <div class="item-title">
                    <a href="{item['url']}" target="_blank">{item['title']}</a>
                </div>
                <div class="summary">{item['summary']}</div>
                <div class="message">
                    <div class="message-label">💡 Engineer's Insight</div>
                    <div class="message-text">{item['message']}</div>
                </div>
                <div class="source">
                    🔗 <a href="{item['url']}" target="_blank">Read Full News</a>
                </div>
            </div>
            """
        html += '</div>'
    
    html += """
            <div class="footer">
                <p>🤖 Automated by GitHub Actions | Powered by Google Gemini AI</p>
                <p>6G Technology Intelligence System for Engineers</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

#!/usr/bin/env python3
"""
시각적으로 개선된 이메일 템플릿
- 카드 스타일 디자인
- 컬러 코딩 (Journal: 파랑, Paper: 초록, News: 주황)
- 아이콘 활용
- 읽기 쉬운 레이아웃
"""
def create_visual_html_email(summary_data):
    """시각적으로 개선된 HTML 이메일 생성"""
    
    # 타입별 색상 및 아이콘 정의
    type_config = {
        'Journal': {
            'color': '#3b82f6',
            'bg_color': '#eff6ff',
            'icon': '📚',
            'label': 'Academic Journal'
        },
        'Paper': {
            'color': '#10b981',
            'bg_color': '#f0fdf4',
            'icon': '📄',
            'label': 'Research Paper'
        },
        'News': {
            'color': '#f59e0b',
            'bg_color': '#fffbeb',
            'icon': '📰',
            'label': 'Industry News'
        }
    }
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #1f2937;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
            }}
            .email-container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            
            /* 헤더 */
            .header {{
                background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }}
            .header::before {{
                content: '';
                position: absolute;
                top: -50%;
                right: -10%;
                width: 200px;
                height: 200px;
                background: rgba(255,255,255,0.1);
                border-radius: 50%;
            }}
            .header::after {{
                content: '';
                position: absolute;
                bottom: -30%;
                left: -5%;
                width: 150px;
                height: 150px;
                background: rgba(255,255,255,0.08);
                border-radius: 50%;
            }}
            .header-content {{
                position: relative;
                z-index: 1;
            }}
            .header h1 {{
                font-size: 32px;
                font-weight: 700;
                margin-bottom: 8px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header-subtitle {{
                font-size: 16px;
                opacity: 0.9;
                font-weight: 300;
            }}
            .header-date {{
                display: inline-block;
                background: rgba(255,255,255,0.2);
                padding: 8px 20px;
                border-radius: 20px;
                margin-top: 16px;
                font-size: 14px;
                backdrop-filter: blur(10px);
            }}
            
            /* 통계 요약 */
            .stats {{
                display: flex;
                justify-content: space-around;
                padding: 30px;
                background: linear-gradient(to bottom, #f9fafb, white);
                border-bottom: 1px solid #e5e7eb;
            }}
            .stat-item {{
                text-align: center;
                padding: 0 20px;
            }}
            .stat-number {{
                font-size: 36px;
                font-weight: 700;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            .stat-label {{
                font-size: 13px;
                color: #6b7280;
                margin-top: 4px;
                font-weight: 500;
            }}
            
            /* 컨텐츠 영역 */
            .content {{
                padding: 30px;
                background-color: #f9fafb;
            }}
            
            /* 섹션 헤더 */
            .section-header {{
                display: flex;
                align-items: center;
                gap: 12px;
                margin: 40px 0 24px 0;
                padding-bottom: 12px;
                border-bottom: 3px solid #e5e7eb;
            }}
            .section-header:first-child {{
                margin-top: 0;
            }}
            .section-icon {{
                font-size: 28px;
            }}
            .section-title {{
                font-size: 22px;
                font-weight: 700;
                color: #1f2937;
            }}
            .section-count {{
                margin-left: auto;
                background: #f3f4f6;
                color: #6b7280;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 600;
            }}
            
            /* 카드 스타일 */
            .card {{
                background: white;
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 20px;
                border: 2px solid #e5e7eb;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            .card::before {{
                content: '';
                position: absolute;
                left: 0;
                top: 0;
                bottom: 0;
                width: 5px;
                background: var(--card-color);
            }}
            .card:hover {{
                box-shadow: 0 12px 24px rgba(0,0,0,0.15);
                transform: translateY(-4px);
                border-color: var(--card-color);
            }}
            
            /* 타입 배지 */
            .type-badge {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                margin-bottom: 12px;
                background: var(--badge-bg);
                color: var(--badge-color);
            }}
            
            /* 카드 제목 */
            .card-title {{
                font-size: 20px;
                font-weight: 700;
                color: #1f2937;
                margin-bottom: 16px;
                line-height: 1.4;
            }}
            .card-title a {{
                color: inherit;
                text-decoration: none;
                transition: color 0.2s;
            }}
            .card-title a:hover {{
                color: var(--card-color);
            }}
            
            /* 카드 내용 */
            .card-summary {{
                color: #4b5563;
                font-size: 15px;
                line-height: 1.7;
                margin-bottom: 16px;
                padding: 16px;
                background: #f9fafb;
                border-radius: 8px;
                border-left: 3px solid var(--card-color);
            }}
            
            /* 인사이트 박스 */
            .insight-box {{
                background: var(--badge-bg);
                border-radius: 8px;
                padding: 16px;
                margin-top: 16px;
                border-left: 3px solid var(--card-color);
            }}
            .insight-label {{
                display: flex;
                align-items: center;
                gap: 6px;
                font-weight: 700;
                color: var(--card-color);
                font-size: 14px;
                margin-bottom: 8px;
            }}
            .insight-text {{
                color: #374151;
                font-size: 14px;
                line-height: 1.6;
            }}
            
            /* 링크 버튼 */
            .card-link {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                margin-top: 16px;
                padding: 10px 20px;
                background: var(--card-color);
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.2s;
            }}
            .card-link:hover {{
                transform: translateX(4px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }}
            
            /* 푸터 */
            .footer {{
                background: #f9fafb;
                padding: 30px;
                text-align: center;
                border-top: 1px solid #e5e7eb;
            }}
            .footer-text {{
                color: #6b7280;
                font-size: 13px;
                margin-bottom: 8px;
            }}
            .footer-logo {{
                font-size: 24px;
                margin-top: 12px;
            }}
            
            /* 반응형 */
            @media (max-width: 600px) {{
                .header h1 {{
                    font-size: 24px;
                }}
                .stats {{
                    flex-direction: column;
                    gap: 20px;
                }}
                .stat-item {{
                    padding: 0;
                }}
                .content {{
                    padding: 20px;
                }}
                .card {{
                    padding: 16px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <!-- 헤더 -->
            <div class="header">
                <div class="header-content">
                    <h1>🔬 6G Technology Intelligence</h1>
                    <div class="header-subtitle">Professional Research Report for Engineers</div>
                    <div class="header-date">📅 {summary_data['generatedAt']}</div>
                </div>
            </div>
            
            <!-- 통계 요약 -->
            <div class="stats">
    """
    
    # 타입별 개수 계산
    type_counts = {'Journal': 0, 'Paper': 0, 'News': 0}
    for item in summary_data['summaries']:
        item_type = item.get('type', 'News')
        type_counts[item_type] = type_counts.get(item_type, 0) + 1
    
    html += f"""
                <div class="stat-item">
                    <div class="stat-number">{type_counts.get('Journal', 0)}</div>
                    <div class="stat-label">📚 Journals</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{type_counts.get('Paper', 0)}</div>
                    <div class="stat-label">📄 Papers</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{type_counts.get('News', 0)}</div>
                    <div class="stat-label">📰 News</div>
                </div>
            </div>
            
            <!-- 컨텐츠 -->
            <div class="content">
    """
    
    # 타입별로 그룹핑
    groups = {'Journal': [], 'Paper': [], 'News': []}
    for item in summary_data['summaries']:
        item_type = item.get('type', 'News')
        groups[item_type].append(item)
    
    # 각 섹션 렌더링
    section_titles = {
        'Journal': '📚 Academic Journals',
        'Paper': '📄 Research Papers',
        'News': '📰 Industry News'
    }
    
    for section_type, items in groups.items():
        if not items:
            continue
            
        config = type_config[section_type]
        
        html += f"""
                <div class="section-header">
                    <span class="section-icon">{config['icon']}</span>
                    <span class="section-title">{section_titles[section_type]}</span>
                    <span class="section-count">{len(items)} items</span>
                </div>
        """
        
        for item in items:
            html += f"""
                <div class="card" style="--card-color: {config['color']}; --badge-bg: {config['bg_color']}; --badge-color: {config['color']};">
                    <div class="type-badge">
                        <span>{config['icon']}</span>
                        <span>{config['label']}</span>
                    </div>
                    
                    <div class="card-title">
                        <a href="{item['url']}" target="_blank">{item['title']}</a>
                    </div>
                    
                    <div class="card-summary">
                        {item['summary']}
                    </div>
                    
                    <div class="insight-box">
                        <div class="insight-label">
                            <span>💡</span>
                            <span>Engineer's Insight</span>
                        </div>
                        <div class="insight-text">
                            {item['message']}
                        </div>
                    </div>
                    
                    <a href="{item['url']}" class="card-link" target="_blank">
                        <span>Read Full Article</span>
                        <span>→</span>
                    </a>
                </div>
            """
    
    html += """
            </div>
            
            <!-- 푸터 -->
            <div class="footer">
                <div class="footer-text">🤖 Automated by GitHub Actions</div>
                <div class="footer-text">Powered by Google Gemini AI</div>
                <div class="footer-logo">🔬 6G Intelligence System</div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

"""
이메일 클라이언트 호환성이 높은 HTML 템플릿
CSS 변수 없이 인라인 스타일 사용
"""

def create_email_safe_html(summary_data, hot_keyword=None):
    """이메일 클라이언트 호환 HTML 생성"""
    
    # 타입별 색상 정의
    colors = {
        'Journal': {
            'primary': '#3b82f6',
            'bg': '#eff6ff',
            'icon': '📚',
            'label': 'Academic Journal'
        },
        'Paper': {
            'primary': '#10b981',
            'bg': '#f0fdf4',
            'icon': '📄',
            'label': 'Research Paper'
        },
        'News': {
            'primary': '#f59e0b',
            'bg': '#fffbeb',
            'icon': '📰',
            'label': 'Industry News'
        }
    }
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px;">
        
        <!-- 메인 컨테이너 -->
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 800px; margin: 0 auto;">
            <tr>
                <td>
                    <table width="100%" cellpadding="0" cellspacing="0" style="background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
                        
                        <!-- 헤더 -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); color: white; padding: 40px 30px; text-align: center;">
                                <h1 style="margin: 0 0 8px 0; font-size: 32px; font-weight: 700;">🔬 6G Technology Intelligence</h1>
                                <p style="margin: 0; font-size: 16px; opacity: 0.9;">Professional Research Report for Engineers</p>
                                <div style="display: inline-block; background: rgba(255,255,255,0.2); padding: 8px 20px; border-radius: 20px; margin-top: 16px; font-size: 14px;">
                                    📅 {summary_data['generatedAt']}
                                </div>
                            </td>
                        </tr>
                        
                        <!-- 통계 요약 -->
                        <tr>
                            <td style="padding: 30px; background: linear-gradient(to bottom, #f9fafb, white); border-bottom: 1px solid #e5e7eb;">
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
    """
    
    # 타입별 개수 계산
    type_counts = {'Journal': 0, 'Paper': 0, 'News': 0}
    for item in summary_data['summaries']:
        item_type = item.get('type', 'News')
        type_counts[item_type] = type_counts.get(item_type, 0) + 1
    
    stats = [
        ('📚 Journals', type_counts.get('Journal', 0)),
        ('📄 Papers', type_counts.get('Paper', 0)),
        ('📰 News', type_counts.get('News', 0))
    ]
    
    for label, count in stats:
        html += f"""
                                        <td style="text-align: center; padding: 0 20px;">
                                            <div style="font-size: 36px; font-weight: 700; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{count}</div>
                                            <div style="font-size: 13px; color: #6b7280; margin-top: 4px; font-weight: 500;">{label}</div>
                                        </td>
        """
    
    html += """
                                    </tr>
                                </table>
                            </td>
                        </tr>
    """

    # Hot Keyword 섹션 추가 (stats 다음)
    if hot_keyword:
        html += f"""
                        <!-- Hot Keyword 섹션 -->
                        <tr>
                            <td style="padding: 20px 30px; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-bottom: 1px solid #e5e7eb;">
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="text-align: center;">
                                            <div style="font-size: 14px; color: #92400e; font-weight: 600; margin-bottom: 4px;">🔥 TODAY'S HOT KEYWORD</div>
                                            <div style="font-size: 18px; font-weight: 700; color: #78350f;">{hot_keyword}</div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
        """

    html += """
                        <!-- 컨텐츠 영역 -->
                        <tr>
                            <td style="padding: 30px; background-color: #f9fafb;">
    """
    
    # 타입별로 그룹핑
    groups = {'Journal': [], 'Paper': [], 'News': []}
    for item in summary_data['summaries']:
        item_type = item.get('type', 'News')
        groups[item_type].append(item)
    
    # 각 섹션 렌더링
    section_titles = {
        'Journal': '📚 Academic Journals',
        'Paper': '📄 Research Papers',
        'News': '📰 Industry News'
    }
    
    for section_type in ['Journal', 'Paper', 'News']:
        items = groups.get(section_type, [])
        if not items:
            continue
        
        color_config = colors[section_type]
        
        # 섹션 헤더
        html += f"""
                                <div style="display: flex; align-items: center; margin: 40px 0 24px 0; padding-bottom: 12px; border-bottom: 3px solid #e5e7eb;">
                                    <span style="font-size: 28px;">{color_config['icon']}</span>
                                    <span style="font-size: 22px; font-weight: 700; color: #1f2937; margin-left: 12px;">{section_titles[section_type]}</span>
                                    <span style="margin-left: auto; background: #f3f4f6; color: #6b7280; padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: 600;">{len(items)} items</span>
                                </div>
        """
        
        # 각 카드
        for item in items:
            html += f"""
                                <!-- 카드 시작 -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="background: white; border-radius: 12px; margin-bottom: 20px; border: 2px solid #e5e7eb; box-shadow: 0 4px 6px rgba(0,0,0,0.07); border-left: 5px solid {color_config['primary']};">
                                    <tr>
                                        <td style="padding: 24px;">
                                            
                                            <!-- 타입 배지 -->
                                            <div style="display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-bottom: 12px; background: {color_config['bg']}; color: {color_config['primary']};">
                                                {color_config['icon']} {color_config['label']}
                                            </div>
                                            
                                            <!-- 제목 -->
                                            <h2 style="margin: 0 0 16px 0; font-size: 20px; font-weight: 700; color: #1f2937; line-height: 1.4;">
                                                <a href="{item['url']}" target="_blank" style="color: #1f2937; text-decoration: none;">{item['title']}</a>
                                            </h2>
                                            
                                            <!-- 요약 -->
                                            <div style="color: #4b5563; font-size: 15px; line-height: 1.7; margin-bottom: 16px; padding: 16px; background: #f9fafb; border-radius: 8px; border-left: 3px solid {color_config['primary']};">
                                                {item['summary']}
                                            </div>
                                            
                                            <!-- 인사이트 -->
                                            <div style="background: {color_config['bg']}; border-radius: 8px; padding: 16px; margin-top: 16px; border-left: 3px solid {color_config['primary']};">
                                                <div style="font-weight: 700; color: {color_config['primary']}; font-size: 14px; margin-bottom: 8px;">
                                                    💡 Engineer's Insight
                                                </div>
                                                <div style="color: #374151; font-size: 14px; line-height: 1.6;">
                                                    {item['message']}
                                                </div>
                                            </div>
                                            
                                            <!-- 링크 버튼 -->
                                            <div style="margin-top: 16px;">
                                                <a href="{item['url']}" target="_blank" style="display: inline-block; padding: 10px 20px; background: {color_config['primary']}; color: white; text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: 600;">
                                                    Read Full Article →
                                                </a>
                                            </div>
                                            
                                        </td>
                                    </tr>
                                </table>
                                <!-- 카드 끝 -->
            """
    
    html += """
                            </td>
                        </tr>
                        
                        <!-- 푸터 -->
                        <tr>
                            <td style="background: #f9fafb; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                                <p style="color: #6b7280; font-size: 13px; margin: 0 0 8px 0;">🤖 Automated by GitHub Actions</p>
                                <p style="color: #6b7280; font-size: 13px; margin: 0 0 12px 0;">Powered by Google Gemini AI</p>
                                <div style="font-size: 24px; margin-top: 12px;">🔬 6G Intelligence System</div>
                            </td>
                        </tr>
                        
                    </table>
                </td>
            </tr>
        </table>
        
    </body>
    </html>
    """
    
    return html

# 기존 fetch_6g_professional.py의 send_email 함수를 이것으로 교체
def send_email(summary_data, hot_keyword=None):
    """시각적으로 개선된 이메일 전송"""
    gmail_user = os.environ.get('GMAIL_USER')
    gmail_password = os.environ.get('GMAIL_APP_PASSWORD')
    recipient = os.environ.get('RECIPIENT_EMAIL')

    if not all([gmail_user, gmail_password, recipient]):
        missing = []
        if not gmail_user: missing.append('GMAIL_USER')
        if not gmail_password: missing.append('GMAIL_APP_PASSWORD')
        if not recipient: missing.append('RECIPIENT_EMAIL')
        print(f"⚠️ 이메일 설정 없음: {', '.join(missing)}. 전송 생략.")
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'🔬 6G Technology Intelligence Report - {summary_data["generatedAt"]}'
    msg['From'] = gmail_user
    msg['To'] = recipient

    # 새로운 시각적 HTML 사용
    html_body = create_email_safe_html(summary_data, hot_keyword=hot_keyword)
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        print("📧 시각적으로 개선된 이메일 전송 중...")
        print(f"   발신: {gmail_user}")
        print(f"   수신: {recipient}")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.set_debuglevel(0)  # 디버그 비활성화
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
        print("✅ 이메일 전송 완료")
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Gmail 인증 실패: {e}")
        print("\n💡 해결 방법:")
        print("1. GMAIL_APP_PASSWORD가 16자리 앱 비밀번호인지 확인하세요 (일반 비밀번호 아님)")
        print("2. Gmail 계정에서 2단계 인증이 활성화되어 있는지 확인하세요")
        print("3. 앱 비밀번호 생성: https://myaccount.google.com/apppasswords")
        print("4. 환경변수 확인: echo $GMAIL_APP_PASSWORD")
    except Exception as e:
        print(f"❌ 이메일 전송 오류: {e}")


# ==================== 텔레그램 전송 ====================
#!/usr/bin/env python3
"""
시각적으로 개선된 텔레그램 메시지
- 이모지 활용
- 명확한 구조
- 읽기 쉬운 포맷
"""

def send_visual_telegram(summary_data, hot_keyword=None):
    """간소화된 텔레그램 메시지 전송 (title, summary, url 포맷)"""

    import requests
    import os
    import html

    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("⚠️ 텔레그램 설정 없음. 전송 생략.")
        return

    # 타입별 그룹핑
    groups = {'Journal': [], 'Paper': [], 'News': []}
    for item in summary_data['summaries']:
        item_type = item.get('type', 'News')
        groups[item_type].append(item)

    # HTML 포맷으로 메시지 작성
    # 헤더와 통계
    header = "🔬 <b>6G Technology Intelligence Report</b>\n"
    header += f"📅 <i>{html.escape(summary_data['generatedAt'])}</i>\n\n"
    header += "📊 <b>Quick Summary</b>\n"
    header += f"├─ 📚 Journals: {len(groups['Journal'])}\n"
    header += f"├─ 📄 Papers: {len(groups['Paper'])}\n"
    header += f"└─ 📰 News: {len(groups['News'])}\n\n"

    # Hot Keyword 섹션
    if hot_keyword:
        header += f"🔥 <b>Today's Hot Keyword:</b> <code>{html.escape(hot_keyword)}</code>\n\n"

    header += "━━━━━━━━━━━━━━━━━━━━\n\n"

    footer = "\n━━━━━━━━━━━━━━━━━━━━\n\n"
    footer += "🤖 <i>Automated Report for 6G Engineers</i>\n"
    footer += "📧 <i>Full details in your email</i>"

    # 텔레그램 메시지 길이 제한 (4096자)
    SAFE_LENGTH = 3500  # footer와 여유 공간 확보

    message = header
    content_parts = []

    # Journal 섹션 (간소화된 포맷: title, summary, url)
    if groups['Journal']:
        section = "📚 <b>ACADEMIC JOURNALS</b>\n\n"
        for i, item in enumerate(groups['Journal'], 1):
            # Title
            title = html.escape(item['title'][:100])
            item_text = f"<b>{i}. {title}</b>\n\n"

            # Summary
            summary = html.escape(item['summary'][:200])
            item_text += f"{summary}...\n\n"

            # URL
            if item.get('url'):
                item_text += f"🔗 <a href=\"{item['url']}\">Read Article</a>\n\n"

            item_text += "─────────────\n\n"

            # 길이 체크
            if len(message + section + item_text + footer) < SAFE_LENGTH:
                section += item_text
            else:
                break

        content_parts.append(section)

    # Paper 섹션 (간소화된 포맷: title, summary, url)
    if groups['Paper']:
        section = "📄 <b>RESEARCH PAPERS</b>\n\n"
        for i, item in enumerate(groups['Paper'], 1):
            # Title
            title = html.escape(item['title'][:100])
            item_text = f"<b>{i}. {title}</b>\n\n"

            # Summary
            summary = html.escape(item['summary'][:200])
            item_text += f"{summary}...\n\n"

            # URL
            if item.get('url'):
                item_text += f"🔗 <a href=\"{item['url']}\">Read Paper</a>\n\n"

            item_text += "─────────────\n\n"

            # 길이 체크
            current_content = ''.join(content_parts) + section + item_text
            if len(message + current_content + footer) < SAFE_LENGTH:
                section += item_text
            else:
                break

        content_parts.append(section)

    # News 섹션 (간소화된 포맷: title, summary, url)
    if groups['News']:
        section = "📰 <b>INDUSTRY NEWS</b>\n\n"
        news_count = 0
        for i, item in enumerate(groups['News'], 1):
            # Title
            title = html.escape(item['title'][:100])
            item_text = f"<b>{i}. {title}</b>\n\n"

            # Summary
            summary = html.escape(item['summary'][:150])
            item_text += f"{summary}...\n\n"

            # URL
            if item.get('url'):
                item_text += f"🔗 <a href=\"{item['url']}\">Read News</a>\n\n"

            item_text += "─────────────\n\n"

            # 길이 체크
            current_content = ''.join(content_parts) + section + item_text
            if len(message + current_content + footer) < SAFE_LENGTH:
                section += item_text
                news_count += 1
            else:
                break

        if len(groups['News']) > news_count:
            section += f"<i>... and {len(groups['News']) - news_count} more news items</i>\n\n"

        content_parts.append(section)

    # 최종 메시지 조립
    message += ''.join(content_parts)
    message += footer

    # 전송
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        print("📱 간소화된 텔레그램 메시지 전송 중...")
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ 텔레그램 전송 완료")
    except Exception as e:
        print(f"❌ 텔레그램 오류: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"응답: {e.response.text}")

# ==================== 파일 저장 ====================

def save_to_file(summary_data):
    """Markdown 파일로 저장"""
    
    os.makedirs('output', exist_ok=True)
    filename = f"output/6g_report_{summary_data['generatedAt']}.md"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# 6G Technology Intelligence Report\n\n")
        f.write(f"**Generated**: {summary_data['generatedAt']}\n")
        f.write(f"**Persona**: 6G Technology Engineer\n\n")
        f.write("---\n\n")
        
        # 타입별 그룹핑
        groups = {'Journal': [], 'Paper': [], 'News': []}
        for item in summary_data['summaries']:
            item_type = item.get('type', 'News')
            groups[item_type].append(item)
        
        # Journal
        if groups['Journal']:
            f.write("## 📚 Academic Journals\n\n")
            for i, item in enumerate(groups['Journal'], 1):
                f.write(f"### {i}. {item['title']}\n\n")
                f.write(f"**제목**: {item['title']}\n\n")
                f.write(f"**요약한 내용**:\n{item['summary']}\n\n")
                f.write(f"**우리에게 주는 메시지**:\n{item['message']}\n\n")
                f.write(f"**출처링크**: {item['url']}\n\n")
                f.write("---\n\n")
        
        # Paper
        if groups['Paper']:
            f.write("## 📄 Research Papers\n\n")
            for i, item in enumerate(groups['Paper'], 1):
                f.write(f"### {i}. {item['title']}\n\n")
                f.write(f"**제목**: {item['title']}\n\n")
                f.write(f"**요약한 내용**:\n{item['summary']}\n\n")
                f.write(f"**우리에게 주는 메시지**:\n{item['message']}\n\n")
                f.write(f"**출처링크**: {item['url']}\n\n")
                f.write("---\n\n")
        
        # News
        if groups['News']:
            f.write("## 📰 Industry News\n\n")
            for i, item in enumerate(groups['News'], 1):
                f.write(f"### {i}. {item['title']}\n\n")
                f.write(f"**제목**: {item['title']}\n\n")
                f.write(f"**요약한 내용**:\n{item['summary']}\n\n")
                f.write(f"**우리에게 주는 메시지**:\n{item['message']}\n\n")
                f.write(f"**출처링크**: {item['url']}\n\n")
                f.write("---\n\n")
    
    print(f"✅ 파일 저장 완료: {filename}")

# ==================== 메인 함수 ====================

def main():
    """메인 실행 함수"""

    print("="*70)
    print("🔬 6G/RAN Technology Intelligence System")
    print("👨‍🏫 Persona: RAN Network Professor & RAN SW Engineer")
    print(f"📅 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    try:
        # Step 1: Hot Keyword 추출
        print("\n" + "="*70)
        print("STEP 1: Hot Keyword 추출")
        print("="*70)
        hot_keyword = extract_hot_keywords()
        print(f"🎯 오늘의 검색 키워드: '{hot_keyword}'")

        # Step 2: 데이터 수집 (각 소스에서 10개씩, 총 30개)
        # Note: Google Scholar removed due to bot detection (429 + CAPTCHA)
        print("\n" + "="*70)
        print("STEP 2: 데이터 수집 (각 소스 10개씩)")
        print("="*70)
        all_items = []

        # IEEE Journals (10개)
        journals = search_ieee(hot_keyword, num_results=10)
        all_items.extend(journals)

        # arXiv Papers (10개)
        papers_arxiv = search_arxiv(hot_keyword, num_results=10)
        all_items.extend(papers_arxiv)

        # Google Scholar Papers - DISABLED (bot detection issues)
        # papers_scholar = search_google_scholar(hot_keyword, num_results=10)
        # all_items.extend(papers_scholar)

        # Google News (10개)
        news = search_google_news(hot_keyword, num_results=10)
        all_items.extend(news)

        print(f"\n✅ 총 {len(all_items)}개 자료 수집 완료")
        print(f"  📚 IEEE Journals: {len(journals)}개")
        print(f"  📄 arXiv Papers: {len(papers_arxiv)}개")
        print(f"  📰 Google News: {len(news)}개")

        if not all_items:
            print("❌ 수집된 자료가 없습니다.")
            return

        # Step 3: RAN SW 개발자 관점에서 Top 10 선별
        print("\n" + "="*70)
        print("STEP 3: RAN SW 개발자 관점 Top 10 선별")
        print("="*70)
        selected_items = select_top_items_for_ran_engineers(all_items, top_n=10)

        print(f"\n선별된 아이템 구성:")
        selected_types = {'Journal': 0, 'Paper': 0, 'News': 0}
        for item in selected_items:
            item_type = item.get('type', 'News')
            selected_types[item_type] = selected_types.get(item_type, 0) + 1

        print(f"  📚 Journals: {selected_types.get('Journal', 0)}개")
        print(f"  📄 Papers: {selected_types.get('Paper', 0)}개")
        print(f"  📰 News: {selected_types.get('News', 0)}개")

        # Step 4: AI 심층 요약
        print("\n" + "="*70)
        print("STEP 4: RAN SW 개발자 관점 심층 요약")
        print("="*70)
        summary_data = summarize_with_gemini(selected_items)

        # Step 5: 파일 저장
        print("\n" + "="*70)
        print("STEP 5: 결과 저장 및 전송")
        print("="*70)
        save_to_file(summary_data)

        # Step 6: 이메일 전송
        send_email(summary_data, hot_keyword=hot_keyword)

        # Step 7: 텔레그램 전송
        send_visual_telegram(summary_data, hot_keyword=hot_keyword)

        print("\n" + "="*70)
        print("✅ 모든 작업 완료!")
        print("="*70)
        print(f"  🔍 Hot Keyword: '{hot_keyword}'")
        print(f"  📊 수집된 자료: {len(all_items)}개")
        print(f"  🎯 선별된 자료: {len(selected_items)}개")
        print(f"  📝 요약 완료: {len(summary_data['summaries'])}개")
        print(f"  💾 파일 저장: ✅")
        print(f"  📧 이메일 전송: ✅")
        print(f"  📱 텔레그램 전송: ✅")
        print("="*70)

    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()