#!/usr/bin/env python3
"""
6G 뉴스 요약 및 이메일 전송 스크립트
매일 자동으로 실행되어 최신 6G 뉴스를 검색하고 이메일로 전송합니다.
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from anthropic import Anthropic

def fetch_6g_news():
    """Anthropic API를 사용하여 6G 뉴스 검색 및 요약"""
    
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    client = Anthropic(api_key=api_key)
    
    print("6G 뉴스 검색 중...")
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search"
        }],
        messages=[{
            "role": "user",
            "content": """Search for the latest 6G technology news and developments from 2025. 
            Then analyze and return ONLY a valid JSON object (no markdown, no backticks) with the top 5 most significant news items.
            
            Use this exact structure:
            {
              "top5": [
                {
                  "title": "News title in English",
                  "summary": "2-3 sentence summary in Korean",
                  "significance": "Why this matters in Korean",
                  "date": "Date or timeframe",
                  "url": "Source URL if available"
                }
              ],
              "generatedAt": "2025-11-22"
            }
            
            Focus on the most recent and impactful 6G developments."""
        }]
    )
    
    # Extract text content
    response_text = ""
    for block in message.content:
        if hasattr(block, 'text'):
            response_text += block.text
    
    # Parse JSON
    clean_text = response_text.replace("```json", "").replace("```", "").strip()
    results = json.loads(clean_text)
    
    print(f"✅ {len(results['top5'])}개 뉴스 발견")
    return results

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
                <p>6G News Summarizer | Powered by Claude AI</p>
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
    
    # 텍스트 본문 (HTML 미지원 클라이언트용)
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
    print("6G 뉴스 요약 및 이메일 전송 시작")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # 1. 뉴스 검색 및 요약
        news_data = fetch_6g_news()
        
        # 2. 파일로 저장
        save_to_file(news_data)
        
        # 3. 이메일 전송
        send_email(news_data)
        
        print("\n" + "="*60)
        print("✅ 모든 작업 완료!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        raise

if __name__ == "__main__":
    main()