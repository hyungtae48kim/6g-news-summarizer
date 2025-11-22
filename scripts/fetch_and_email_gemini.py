#!/usr/bin/env python3
"""
6G 뉴스 요약 및 이메일 전송 스크립트 (Google Gemini 무료 버전)
매일 자동으로 실행되어 최신 6G 뉴스를 검색하고 이메일로 전송합니다.
"""

import os
import json
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from bs4 import BeautifulSoup

def search_google_news(query, num_results=10):
    """Google 뉴스에서 6G 관련 뉴스 검색"""
    
    print(f"구글 뉴스 검색 중: {query}")
    
    # Google News RSS를 사용한 검색
    url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item', limit=num_results)
        
        results = []
        for item in items:
            results.append({
                'title': item.title.text if item.title else '',
                'link': item.link.text if item.link else '',
                'pub_date': item.pubDate.text if item.pubDate else '',
                'description': item.description.text if item.description else ''
            })
        
        print(f"✅ {len(results)}개 뉴스 발견")
        return results
        
    except Exception as e:
        print(f"❌ 검색 오류: {e}")
        return []

def fetch_6g_news_with_gemini():
    """Google Gemini API를 사용하여 뉴스 분석 및 요약"""
    
    api_key = os.environ.get('GEMINI_API_KEY')
    
    # 6G 뉴스 검색
    news_items = search_google_news("6G technology 2025", num_results=15)
    
    if not news_items:
        print("뉴스를 찾지 못했습니다.")
        return get_empty_news()
    
    # API 키가 없거나 비어있으면 웹 스크래핑 결과만 사용
    if not api_key or api_key.strip() == '':
        print("⚠️ GEMINI_API_KEY가 설정되지 않았습니다. 웹 스크래핑 결과만 사용합니다.")
        return create_summary_from_news(news_items[:5])
    
    # 뉴스 요약을 위한 프롬프트 생성
    news_context = "\n\n".join([
        f"제목: {item['title']}\n링크: {item['link']}\n날짜: {item['pub_date']}\n설명: {item['description']}"
        for item in news_items
    ])
    
    prompt = f"""다음은 최신 6G 기술 관련 뉴스입니다. 이 중에서 가장 중요하고 영향력 있는 TOP 5 뉴스를 선정하고, 각각을 한국어로 요약해주세요.

뉴스 목록:
{news_context}

다음 JSON 형식으로만 답변해주세요 (마크다운이나 백틱 없이):
{{
  "top5": [
    {{
      "title": "뉴스 제목 (영어 원문)",
      "summary": "2-3문장의 한국어 요약",
      "significance": "이 뉴스가 중요한 이유 (한국어)",
      "date": "날짜",
      "url": "원문 링크"
    }}
  ],
  "generatedAt": "{datetime.now().strftime('%Y-%m-%d')}"
}}

가장 최근이고 영향력 있는 뉴스 위주로 선정해주세요."""

    # Gemini API 호출
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.4,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 2048,
        }
    }
    
    print("Gemini API로 뉴스 분석 중...")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        # API 키 오류 체크
        if response.status_code == 400:
            error_data = response.json()
            print(f"❌ API 키 오류: {error_data}")
            print("⚠️ 웹 스크래핑 결과만 사용합니다.")
            return create_summary_from_news(news_items[:5])
        
        response.raise_for_status()
        
        data = response.json()
        print(f"API 응답 구조: {json.dumps(data, indent=2)[:500]}")  # 디버깅용
        
        # 응답에서 텍스트 추출 (안전하게)
        try:
            if 'candidates' in data and len(data['candidates']) > 0:
                candidate = data['candidates'][0]
                
                # content 구조 확인
                if 'content' in candidate:
                    content = candidate['content']
                    
                    # parts가 있는 경우
                    if 'parts' in content and len(content['parts']) > 0:
                        text = content['parts'][0].get('text', '')
                    # text가 직접 있는 경우
                    elif 'text' in content:
                        text = content['text']
                    else:
                        print(f"❌ 알 수 없는 content 구조: {content}")
                        return create_summary_from_news(news_items[:5])
                        
                # output 또는 text 필드가 직접 있는 경우
                elif 'output' in candidate:
                    text = candidate['output']
                elif 'text' in candidate:
                    text = candidate['text']
                else:
                    print(f"❌ 알 수 없는 응답 구조: {candidate}")
                    return create_summary_from_news(news_items[:5])
                
                if not text:
                    print("❌ 빈 응답")
                    return create_summary_from_news(news_items[:5])
                
                # JSON 파싱
                clean_text = text.replace("```json", "").replace("```", "").strip()
                results = json.loads(clean_text)
                
                print(f"✅ {len(results['top5'])}개 뉴스 분석 완료")
                return results
                
            else:
                print(f"❌ candidates 없음: {data}")
                return create_summary_from_news(news_items[:5])
                
        except (KeyError, IndexError, TypeError) as e:
            print(f"❌ 응답 파싱 오류: {e}")
            print(f"응답 데이터: {data}")
            return create_summary_from_news(news_items[:5])
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Gemini API 오류: {e}")
        print("⚠️ 웹 스크래핑 결과만 사용합니다.")
        return create_summary_from_news(news_items[:5])
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        print(f"응답 텍스트: {text[:200] if 'text' in locals() else 'N/A'}")
        return create_summary_from_news(news_items[:5])

def create_summary_from_news(news_items):
    """웹 스크래핑 결과로부터 직접 요약본 생성 (AI 없이)"""
    
    print("웹 스크래핑 결과로 요약본 생성 중...")
    
    results = {
        "top5": [],
        "generatedAt": datetime.now().strftime('%Y-%m-%d')
    }
    
    for i, item in enumerate(news_items[:5], 1):
        # 설명이 너무 길면 자르기
        description = item['description']
        if len(description) > 250:
            description = description[:250] + "..."
        
        results["top5"].append({
            "title": item['title'],
            "summary": description,
            "significance": f"6G 기술 발전의 최신 동향을 보여주는 {i}번째 주요 뉴스",
            "date": item['pub_date'],
            "url": item['link']
        })
    
    print(f"✅ {len(results['top5'])}개 뉴스 요약 완료 (AI 요약 없음)")
    return results

def get_empty_news():
    """뉴스가 없을 때 기본 데이터"""
    return {
        "top5": [{
            "title": "6G 뉴스를 찾을 수 없습니다",
            "summary": "현재 6G 관련 최신 뉴스를 검색할 수 없습니다. 나중에 다시 시도해주세요.",
            "significance": "시스템 오류",
            "date": datetime.now().strftime('%Y-%m-%d'),
            "url": "https://news.google.com"
        }],
        "generatedAt": datetime.now().strftime('%Y-%m-%d')
    }

def create_html_email(news_data):
    """HTML 형식의 이메일 생성"""
    
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
                max-width: 800px;
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
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
            .date {{
                color: #e0e0e0;
                font-size: 14px;
                margin-top: 10px;
            }}
            .news-item {{
                background-color: #f9f9f9;
                border-left: 4px solid #667eea;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 5px;
            }}
            .news-number {{
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                width: 35px;
                height: 35px;
                border-radius: 50%;
                text-align: center;
                line-height: 35px;
                font-weight: bold;
                margin-right: 15px;
                font-size: 18px;
            }}
            .news-title {{
                color: #2c3e50;
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .news-title a {{
                color: #667eea;
                text-decoration: none;
            }}
            .news-title a:hover {{
                text-decoration: underline;
            }}
            .news-summary {{
                color: #555;
                margin-bottom: 15px;
            }}
            .significance {{
                background-color: #e3f2fd;
                border-left: 3px solid #2196f3;
                padding: 10px 15px;
                margin-bottom: 10px;
                border-radius: 3px;
            }}
            .significance strong {{
                color: #1976d2;
            }}
            .source {{
                background-color: #f5f5f5;
                padding: 10px 15px;
                border-radius: 3px;
                font-size: 13px;
                word-break: break-all;
            }}
            .source strong {{
                color: #666;
            }}
            .source a {{
                color: #667eea;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
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
                <h1>🌐 6G 기술 뉴스 요약</h1>
                <div class="date">생성일: {news_data['generatedAt']}</div>
            </div>
    """
    
    for i, news in enumerate(news_data['top5'], 1):
        url_link = f'<a href="{news["url"]}" target="_blank">{news["title"]}</a>' if news.get('url') else news['title']
        
        html += f"""
            <div class="news-item">
                <div>
                    <span class="news-number">{i}</span>
                    <span class="news-title">{url_link}</span>
                </div>
                {f'<div style="color: #888; font-size: 13px; margin: 10px 0 10px 50px;">{news["date"]}</div>' if news.get('date') else ''}
                <div class="news-summary" style="margin-left: 50px;">
                    {news['summary']}
                </div>
                <div class="significance" style="margin-left: 50px;">
                    <strong>💡 중요도:</strong> {news['significance']}
                </div>
                {f'<div class="source" style="margin-left: 50px;"><strong>📰 출처:</strong> <a href="{news["url"]}" target="_blank">{news["url"]}</a></div>' if news.get('url') else ''}
            </div>
        """
    
    html += """
            <div class="footer">
                <p>이 이메일은 GitHub Actions를 통해 자동으로 생성되었습니다.</p>
                <p>6G News Summarizer | Powered by Google Gemini (Free)</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def send_email(news_data):
    """Gmail을 통해 이메일 전송"""
    
    gmail_user = os.environ.get('GMAIL_USER')
    gmail_password = os.environ.get('GMAIL_APP_PASSWORD')
    recipient = os.environ.get('RECIPIENT_EMAIL')
    
    if not all([gmail_user, gmail_password, recipient]):
        raise ValueError("이메일 관련 환경 변수가 설정되지 않았습니다.")
    
    # 이메일 생성
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'📡 6G 기술 뉴스 요약 - {news_data["generatedAt"]}'
    msg['From'] = gmail_user
    msg['To'] = recipient
    
    # HTML 본문
    html_body = create_html_email(news_data)
    
    # 텍스트 본문
    text_body = f"""
6G 기술 뉴스 요약
생성일: {news_data['generatedAt']}

"""
    
    for i, news in enumerate(news_data['top5'], 1):
        text_body += f"""
{i}. {news['title']}
{news.get('date', '')}

{news['summary']}

💡 중요도: {news['significance']}
"""
        if news.get('url'):
            text_body += f"📰 출처: {news['url']}\n"
        text_body += "\n" + "="*60 + "\n\n"
    
    text_body += "\n이 이메일은 GitHub Actions를 통해 자동으로 생성되었습니다."
    
    # 본문 추가
    msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    
    # 이메일 전송
    print(f"이메일 전송 중: {recipient}")
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(gmail_user, gmail_password)
        server.send_message(msg)
    
    print("✅ 이메일 전송 완료")

def save_to_file(news_data):
    """결과를 파일로 저장"""
    
    os.makedirs('output', exist_ok=True)
    
    filename = f"output/6g_news_{news_data['generatedAt']}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"6G 기술 뉴스 요약\n")
        f.write(f"생성일: {news_data['generatedAt']}\n")
        f.write("="*60 + "\n\n")
        
        for i, news in enumerate(news_data['top5'], 1):
            f.write(f"{i}. {news['title']}\n")
            if news.get('date'):
                f.write(f"날짜: {news['date']}\n")
            f.write(f"\n{news['summary']}\n\n")
            f.write(f"💡 중요도: {news['significance']}\n")
            if news.get('url'):
                f.write(f"📰 출처: {news['url']}\n")
            f.write("\n" + "="*60 + "\n\n")
    
    print(f"✅ 파일 저장 완료: {filename}")

def main():
    """메인 실행 함수"""
    
    print("="*60)
    print("6G 뉴스 요약 및 이메일 전송 시작 (Google Gemini 무료 버전)")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # 1. 뉴스 검색 및 요약
        news_data = fetch_6g_news_with_gemini()
        
        # 2. 파일로 저장
        save_to_file(news_data)
        
        # 3. 이메일 전송
        send_email(news_data)
        
        print("\n" + "="*60)
        print("✅ 모든 작업 완료!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()