#!/usr/bin/env python3
"""
6G 기술 전문 검색 및 요약 시스템 (Engineer Persona)
Journal, Paper, News 각 5개씩 총 15개 수집 및 요약
"""

import os
import json
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from urllib.parse import unquote


def search_ieee(query, num_results=5):
    """IEEE Xplore 검색 (Journals) - Selenium 사용"""
    
    print(f"📰 IEEE Xplore 검색 중: {query}")
    
    # Chrome 옵션 설정
    options = Options()
    options.add_argument('--headless')  # 백그라운드 실행
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    if os.environ.get('GITHUB_ACTIONS') == 'true':
        options.binary_location = '/usr/bin/chromium-browser'

    driver = None
    
    try:
        # 🆕 GitHub Actions용 ChromeDriver 경로
        if os.environ.get('GITHUB_ACTIONS') == 'true':
            from selenium.webdriver.chrome.service import Service
            service = Service('/usr/bin/chromedriver')
            driver = webdriver.Chrome(service=service, options=options)
        else:
            # 로컬 환경
            from webdriver_manager.chrome import ChromeDriverManager
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
        
        # Google을 통한 IEEE 논문 검색
        search_query = query.replace(' ', '+')
        search_url = f"https://www.google.com/search?q=site:ieeexplore.ieee.org+{search_query}"
        
        driver.get(search_url)
        
        # 페이지 로딩 대기 (CAPTCHA 회피)
        time.sleep(3)
        
        results = []
        
        # 여러 가능한 CSS 선택자 시도 (Google 구조 변경 대응)
        selectors = [
            'div.g',                          # 기존 구조
            'div[data-sokoban-container]',    # 최신 구조 1
            'div.MjjYud',                     # 최신 구조 2
            'div.Gx5Zad'                      # 대체 구조
        ]
        
        search_results = []
        used_selector = None
        
        for selector in selectors:
            try:
                search_results = driver.find_elements(By.CSS_SELECTOR, selector)
                if len(search_results) > 0:
                    used_selector = selector
                    print(f"  ✓ 선택자 '{selector}' 사용: {len(search_results)}개 발견")
                    break
            except Exception as e:
                continue
        
        if not search_results:
            print("  ⚠️ 검색 결과를 찾을 수 없습니다")
        
        # 결과 파싱
        parsed_count = 0
        for result in search_results:
            if len(results) >= num_results:
                break
            
            try:
                # 제목 추출 (h3, h2 태그 시도)
                title_elem = None
                title = None
                
                for tag in ['h3', 'h2', 'h1']:
                    try:
                        title_elem = result.find_element(By.TAG_NAME, tag)
                        if title_elem and title_elem.text.strip():
                            title = title_elem.text.strip()
                            break
                    except:
                        continue
                
                # 링크 추출
                url = None
                try:
                    link_elem = result.find_element(By.TAG_NAME, 'a')
                    url = link_elem.get_attribute('href')
                    
                    # Google 리디렉션 URL 정제
                    if url and '/url?q=' in url:
                        match = re.search(r'/url\?q=(.*?)&', url)
                        if match:
                            url = match.group(1)
                    
                    # URL 디코딩
                    if url:
                        from urllib.parse import unquote
                        url = unquote(url)
                        
                except:
                    pass
                
                # IEEE URL 및 제목 검증
                if url and 'ieeexplore.ieee.org' in url and title:
                    # 설명/요약 추출 (선택적)
                    description = title
                    try:
                        # 여러 가능한 설명 요소 시도
                        snippet_selectors = [
                            'div.VwiC3b',
                            'span.aCOpRe',
                            'div.IsZvec',
                            'div.s'
                        ]
                        
                        for snippet_sel in snippet_selectors:
                            try:
                                snippet_elem = result.find_element(By.CSS_SELECTOR, snippet_sel)
                                if snippet_elem and snippet_elem.text.strip():
                                    description = snippet_elem.text.strip()
                                    break
                            except:
                                continue
                    except:
                        pass
                    
                    results.append({
                        'title': title,
                        'description': description,
                        'url': url,
                        'type': 'Journal'
                    })
                    
                    parsed_count += 1
                    
            except Exception as e:
                # 개별 결과 파싱 실패는 무시
                continue
        
        print(f"  📊 파싱 성공: {parsed_count}개")
        
        # 결과가 부족하면 Google Scholar 추가 검색
        if len(results) < num_results:
            print(f"⚠️ IEEE 결과 부족 ({len(results)}개), Google Scholar에서 추가 검색...")
            try:
                scholar_results = search_google_scholar(f"{query} IEEE", num_results - len(results))
                results.extend(scholar_results)
            except Exception as e:
                print(f"  ⚠️ Google Scholar 추가 검색 실패: {e}")
        
        print(f"✅ {len(results)}개 저널 발견")
        return results
        
    except Exception as e:
        print(f"❌ IEEE 검색 오류: {e}")
        import traceback
        traceback.print_exc()
        
        # 대체: Google Scholar에서 IEEE 논문 검색
        print("⚠️ Google Scholar로 대체 검색...")
        try:
            return search_google_scholar(f"{query} IEEE journal", num_results)
        except:
            return []
        
    finally:
        # 드라이버 종료 (리소스 정리)
        if driver:
            try:
                driver.quit()
            except:
                pass


def search_google_scholar(query, num_results=5):
    """
    Google Scholar 검색 - Selenium 버전
    기존 scholarly 라이브러리 대신 사용 가능
    """
    
    print(f"📚 Google Scholar 검색 중: {query}")
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-gpu')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = None
    
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        # Google Scholar 검색
        search_query = query.replace(' ', '+')
        search_url = f"https://scholar.google.com/scholar?q={search_query}&hl=en"
        
        driver.get(search_url)
        
        # 페이지 로딩 대기
        time.sleep(3)
        
        # CAPTCHA 확인
        page_source = driver.page_source.lower()
        if "unusual traffic" in page_source or "captcha" in page_source:
            print("  ⚠️ Google Scholar CAPTCHA 감지됨 - 결과 제한될 수 있음")
            # CAPTCHA가 있어도 일부 결과는 파싱 시도
        
        results = []
        
        # Google Scholar 검색 결과 파싱
        try:
            # 검색 결과 컨테이너
            search_results = driver.find_elements(By.CSS_SELECTOR, 'div.gs_ri')
            
            print(f"  📊 Scholar 결과 발견: {len(search_results)}개")
            
            for result in search_results[:num_results * 2]:  # 여유있게 가져오기
                if len(results) >= num_results:
                    break
                
                try:
                    # 제목
                    title = None
                    url = None
                    
                    try:
                        title_elem = result.find_element(By.CSS_SELECTOR, 'h3.gs_rt')
                        title = title_elem.text.strip()
                        
                        # URL 추출
                        try:
                            link = title_elem.find_element(By.TAG_NAME, 'a')
                            url = link.get_attribute('href')
                        except:
                            pass
                    except:
                        continue
                    
                    if not title:
                        continue
                    
                    # 설명/초록
                    description = title
                    try:
                        desc_elem = result.find_element(By.CSS_SELECTOR, 'div.gs_rs')
                        if desc_elem and desc_elem.text.strip():
                            description = desc_elem.text.strip()
                    except:
                        pass
                    
                    # 저자 정보
                    authors = ""
                    try:
                        authors_elem = result.find_element(By.CSS_SELECTOR, 'div.gs_a')
                        if authors_elem:
                            authors = authors_elem.text.strip()
                    except:
                        pass
                    
                    results.append({
                        'title': title,
                        'description': description,
                        'url': url if url else '',
                        'type': 'Journal',
                        'authors': authors
                    })
                    
                except Exception as e:
                    continue
            
            print(f"✅ {len(results)}개 논문 발견")
            return results
            
        except Exception as e:
            print(f"  ❌ Scholar 파싱 오류: {e}")
            return []
        
    except Exception as e:
        print(f"❌ Google Scholar 검색 오류: {e}")
        import traceback
        traceback.print_exc()
        return []
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


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
            results.append({
                'title': item.title.text if item.title else '',
                'description': item.description.text if item.description else '',
                'url': item.link.text if item.link else '',
                'pub_date': item.pubDate.text if item.pubDate else '',
                'type': 'News'
            })
        
        print(f"✅ {len(results)}개 뉴스 발견")
        return results
        
    except Exception as e:
        print(f"❌ Google News 검색 오류: {e}")
        return []

# ==================== AI 요약 함수 ====================

def summarize_with_gemini(items):
    """Gemini AI로 6G 엔지니어 관점 요약"""
    
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key:
        print("⚠️ GEMINI_API_KEY 없음. AI 요약 생략.")
        return create_summary_without_ai(items)
    
    # 아이템 정보 구성 (특수문자 이스케이프)
    items_context = ""
    for i, item in enumerate(items, 1):
        # 특수문자 제거 및 이스케이프
        title = item['title'].replace('"', '\\"').replace("'", "\\'").replace('\n', ' ').strip()[:200]
        description = item['description'].replace('"', '\\"').replace("'", "\\'").replace('\n', ' ').strip()[:300]
        url = item['url'].replace('"', '\\"').strip()
        
        items_context += f"\n{i}. [{item['type']}] {title}\n"
        items_context += f"Description: {description}\n"
        items_context += f"Link: {url}\n"
    
    prompt = f"""당신은 6G 기술을 연구하는 전문 엔지니어입니다.

다음 6G 관련 자료들(Journal, Paper, News)을 분석하고 각각 요약해주세요.

자료 목록:
{items_context}

각 자료에 대해 다음 형식으로 요약하세요. 반드시 JSON 형식만 반환하고 다른 텍스트는 포함하지 마세요:

{{
  "summaries": [
    {{
      "title": "논문 또는 저널 또는 뉴스 제목",
      "summary": "핵심 내용을 3-4문장으로 요약 (한국어)",
      "message": "이 자료가 6G 엔지니어에게 주는 핵심 메시지와 실무적 시사점 (한국어)",
      "url": "원문 링크",
      "type": "Journal 또는 Paper 또는 News"
    }}
  ],
  "generatedAt": "{datetime.now().strftime('%Y-%m-%d')}"
}}

엔지니어 관점에서 기술적 통찰과 실무 적용 가능성을 중심으로 분석하세요."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 8192,
        }
    }
    
    try:
        print("🤖 Gemini AI로 요약 중...")
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        if 'candidates' in data and len(data['candidates']) > 0:
            candidate = data['candidates'][0]
            
            if 'content' in candidate and 'parts' in candidate['content']:
                text = candidate['content']['parts'][0].get('text', '')
                
                # JSON 파싱
                clean_text = text.replace("```json", "").replace("```", "").strip()
                
                # 파싱 전 디버깅
                print(f"응답 텍스트 길이: {len(clean_text)}")
                
                try:
                    results = json.loads(clean_text)
                    print(f"✅ {len(results['summaries'])}개 요약 완료")
                    return results
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 파싱 오류: {e}")
                    print(f"응답 미리보기: {clean_text[:500]}")
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
    
    for section_type in ['Journal', 'Paper', 'News']:
        items = groups.get(section_type, [])
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

def create_email_safe_html(summary_data):
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
def send_email(summary_data):
    """시각적으로 개선된 이메일 전송"""
    gmail_user = os.environ.get('GMAIL_USER')
    gmail_password = os.environ.get('GMAIL_APP_PASSWORD')
    recipient = os.environ.get('RECIPIENT_EMAIL')
    
    if not all([gmail_user, gmail_password, recipient]):
        print("⚠️ 이메일 설정 없음. 전송 생략.")
        return
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'🔬 6G Technology Intelligence Report - {summary_data["generatedAt"]}'
    msg['From'] = gmail_user
    msg['To'] = recipient
    
    # 새로운 시각적 HTML 사용
    html_body = create_email_safe_html(summary_data)
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    
    try:
        print("📧 시각적으로 개선된 이메일 전송 중...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
        print("✅ 이메일 전송 완료")
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

def send_visual_telegram(summary_data):
    """시각적으로 개선된 텔레그램 메시지 전송"""
    
    import requests
    import os
    
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
    
    # 헤더 메시지
    message = "🔬 *6G Technology Intelligence Report*\n"
    message += f"📅 _{summary_data['generatedAt']}_\n\n"
    
    # 통계 요약
    message += "📊 *Quick Summary*\n"
    message += f"├─ 📚 Journals: {len(groups['Journal'])}\n"
    message += f"├─ 📄 Papers: {len(groups['Paper'])}\n"
    message += f"└─ 📰 News: {len(groups['News'])}\n\n"
    message += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Journal 섹션
    if groups['Journal']:
        message += "📚 *ACADEMIC JOURNALS*\n\n"
        for i, item in enumerate(groups['Journal'], 1):
            # 제목
            title = item['title'][:80].replace('_', '\\_').replace('*', '\\*').replace('[', '\\[')
            message += f"*{i}\\. {title}*\n\n"
            
            # 요약 (짧게)
            summary = item['summary'][:120].replace('_', '\\_').replace('*', '\\*')
            message += f"📝 {summary}\\.\\.\\.\n\n"
            
            # 인사이트
            insight = item['message'][:100].replace('_', '\\_').replace('*', '\\*')
            message += f"💡 _{insight}_\n\n"
            
            # 링크
            if item.get('url'):
                message += f"🔗 [Read Full Article]({item['url']})\n\n"
            
            message += "─────────────\n\n"
    
    # Paper 섹션
    if groups['Paper']:
        message += "📄 *RESEARCH PAPERS*\n\n"
        for i, item in enumerate(groups['Paper'], 1):
            title = item['title'][:80].replace('_', '\\_').replace('*', '\\*').replace('[', '\\[')
            message += f"*{i}\\. {title}*\n\n"
            
            summary = item['summary'][:120].replace('_', '\\_').replace('*', '\\*')
            message += f"📝 {summary}\\.\\.\\.\n\n"
            
            insight = item['message'][:100].replace('_', '\\_').replace('*', '\\*')
            message += f"💡 _{insight}_\n\n"
            
            if item.get('url'):
                message += f"🔗 [Read Paper]({item['url']})\n\n"
            
            message += "─────────────\n\n"
    
    # News 섹션 (최대 3개)
    if groups['News']:
        message += "📰 *INDUSTRY NEWS*\n\n"
        for i, item in enumerate(groups['News'][:3], 1):
            title = item['title'][:70].replace('_', '\\_').replace('*', '\\*').replace('[', '\\[')
            message += f"*{i}\\. {title}*\n"
            
            if item.get('url'):
                message += f"🔗 [Read More]({item['url']})\n\n"
        
        if len(groups['News']) > 3:
            message += f"_\\.\\.\\. and {len(groups['News']) - 3} more news items_\n\n"
    
    message += "━━━━━━━━━━━━━━━━━━━━\n\n"
    message += "🤖 _Automated Report for 6G Engineers_\n"
    message += "📧 _Full details in your email_"
    
    # 메시지 길이 제한 (4096자)
    if len(message) > 4000:
        message = message[:3900] + "\\.\\.\\.\n\n_\\(Full report in email\\)_"
    
    # 전송
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True  # 미리보기 비활성화로 깔끔하게
    }
    
    try:
        print("📱 시각적으로 개선된 텔레그램 전송 중...")
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
    
    print("="*60)
    print("6G Technology Intelligence System")
    print("Persona: 6G Technology Research Engineer")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # 1. 데이터 수집 (총 15개)
        all_items = []
        
        # Papers (5개) - 먼저 수집 (더 신뢰성 높음)
        print("\n📄 Research Papers 검색 중...")
        papers_arxiv = search_arxiv("6G wireless", num_results=3)
        papers_scholar = search_google_scholar("6G technology 2025", num_results=2)
        all_items.extend(papers_arxiv)
        all_items.extend(papers_scholar)
        
        # Journals (5개) - IEEE + Scholar 혼합
        print("\n📚 Academic Journals 검색 중...")
        journals = []
        # IEEE에서 2-3개 시도
        ieee_results = search_ieee("6G wireless communications", num_results=3)
        journals.extend(ieee_results)
        # Google Scholar에서 추가
        if len(journals) < 5:
            scholar_journals = search_google_scholar("6G network architecture journal", num_results=5-len(journals))
            # Journal로 타입 변경
            for item in scholar_journals:
                item['type'] = 'Journal'
            journals.extend(scholar_journals)
        all_items.extend(journals[:5])
        
        # News (5개)
        print("\n📰 Industry News 검색 중...")
        news = search_google_news("6G technology 2025", num_results=5)
        all_items.extend(news)
        
        print(f"\n✅ 총 {len(all_items)}개 자료 수집 완료")
        print(f"  - Journals: {len(journals)}개")
        print(f"  - Papers: {len(papers_arxiv) + len(papers_scholar)}개")
        print(f"  - News: {len(news)}개")
        
        if not all_items:
            print("❌ 수집된 자료가 없습니다.")
            return
        
        # 2. AI 요약
        summary_data = summarize_with_gemini(all_items)
        
        # 3. 파일 저장
        save_to_file(summary_data)
        
        # 4. 이메일 전송
        send_email(summary_data)
        
        # 5. 텔레그램 전송
        send_visual_telegram(summary_data)
        
        print("\n" + "="*60)
        print("✅ 모든 작업 완료!")
        print(f"  - 자료 수집: {len(all_items)}개")
        print(f"  - AI 요약: {len(summary_data['summaries'])}개")
        print(f"  - 파일 저장: ✅")
        print(f"  - 이메일 전송: ✅")
        print(f"  - 텔레그램 전송: ✅")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()