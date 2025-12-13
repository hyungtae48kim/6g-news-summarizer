#!/usr/bin/env python3
"""
뉴스 URL 검증 테스트 스크립트
- Google News와 The Verge에서 실제 뉴스 URL 추출
- URL이 홈페이지가 아닌 실제 기사로 연결되는지 확인
- 문제가 있는 URL 진단 및 보고
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

def validate_and_clean_url(url):
    """URL 유효성 검증 및 정제 (메인 스크립트와 동일)"""
    if not url:
        return ''

    url = url.strip()

    try:
        if not url.startswith(('http://', 'https://')):
            return ''

        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if not url_pattern.match(url):
            return ''

        return url

    except Exception as e:
        print(f"⚠️ URL 검증 오류: {str(e)[:50]}")
        return ''

def is_homepage_url(url):
    """URL이 홈페이지인지 확인 (경로가 없거나 루트만 있는 경우)"""
    try:
        parsed = urlparse(url)
        path = parsed.path.strip('/')

        # 경로가 없거나 빈 경우
        if not path:
            return True, "루트 경로 (홈페이지)"

        # 경로가 매우 짧은 경우 (홈페이지 가능성 높음)
        if len(path) < 5:
            return True, f"경로가 너무 짧음: '{path}'"

        # 일반적인 홈페이지 경로
        homepage_paths = ['index.html', 'index.php', 'home', 'main']
        if path.lower() in homepage_paths:
            return True, f"홈페이지 경로: '{path}'"

        return False, f"기사 경로: '{path}'"

    except Exception as e:
        return False, f"파싱 오류: {str(e)}"

def test_google_news_urls(query="6G wireless", num_results=5):
    """Google News RSS에서 URL 추출 및 검증"""

    print("\n" + "="*70)
    print("🧪 Google News URL 테스트")
    print("="*70)
    print(f"검색어: {query}")
    print(f"결과 수: {num_results}")
    print()

    url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"

    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item', limit=num_results)

        results = []
        for i, item in enumerate(items, 1):
            title = item.title.text if item.title else 'No title'

            # Method 1: Extract from <source> tag
            source_tag = item.find('source')
            source_url = source_tag.get('url') if source_tag else None

            # Method 2: Extract from <link> tag (Google redirect)
            link_url = item.link.text if item.link else None

            # Validate both URLs
            validated_source = validate_and_clean_url(source_url) if source_url else ''
            validated_link = validate_and_clean_url(link_url) if link_url else ''

            # Check if homepage
            is_homepage_source, source_reason = is_homepage_url(validated_source) if validated_source else (None, 'No URL')
            is_homepage_link, link_reason = is_homepage_url(validated_link) if validated_link else (None, 'No URL')

            result = {
                'index': i,
                'title': title[:80] + '...' if len(title) > 80 else title,
                'source_url': validated_source,
                'link_url': validated_link,
                'is_homepage_source': is_homepage_source,
                'source_reason': source_reason,
                'is_homepage_link': is_homepage_link,
                'link_reason': link_reason
            }
            results.append(result)

            # 출력
            print(f"{i}. {result['title']}")
            print(f"   Source URL: {validated_source or '❌ 없음'}")
            if validated_source:
                status = "⚠️ 홈페이지" if is_homepage_source else "✅ 기사"
                print(f"   └─ {status}: {source_reason}")

            print(f"   Link URL: {validated_link or '❌ 없음'}")
            if validated_link:
                status = "⚠️ 리다이렉트" if 'news.google.com' in validated_link else "✅ 직접 링크"
                print(f"   └─ {status}")
            print()

        # 통계
        total = len(results)
        homepage_count = sum(1 for r in results if r['is_homepage_source'])
        valid_count = total - homepage_count

        print("📊 통계:")
        print(f"   전체: {total}개")
        print(f"   ✅ 유효한 기사 URL: {valid_count}개")
        print(f"   ⚠️ 홈페이지 URL: {homepage_count}개")

        return results

    except Exception as e:
        print(f"❌ Google News 테스트 오류: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_verge_urls(query="6G wireless", num_results=5):
    """The Verge Atom feed에서 URL 추출 및 검증"""

    print("\n" + "="*70)
    print("🧪 The Verge URL 테스트")
    print("="*70)
    print(f"필터링: {query}")
    print(f"결과 수: {num_results}")
    print()

    url = "https://www.theverge.com/rss/index.xml"

    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'xml')
        entries = soup.find_all('entry')

        results = []
        query_lower = query.lower()

        for entry in entries:
            if len(results) >= num_results:
                break

            title = entry.find('title').text if entry.find('title') else ''
            summary_elem = entry.find('summary')
            content_elem = entry.find('content')

            description = ''
            if summary_elem:
                description = summary_elem.text
            elif content_elem:
                description = BeautifulSoup(content_elem.text, 'html.parser').get_text()

            # Filter by query
            text_to_search = (title + ' ' + description).lower()
            query_words = query_lower.split()

            if not any(word in text_to_search for word in query_words):
                continue

            # Extract URL
            link_elem = entry.find('link', {'rel': 'alternate'})
            if not link_elem:
                link_elem = entry.find('link')

            extracted_url = link_elem.get('href') if link_elem else ''
            validated_url = validate_and_clean_url(extracted_url)

            # Check if homepage
            is_homepage, reason = is_homepage_url(validated_url) if validated_url else (None, 'No URL')

            result = {
                'index': len(results) + 1,
                'title': title[:80] + '...' if len(title) > 80 else title,
                'url': validated_url,
                'is_homepage': is_homepage,
                'reason': reason
            }
            results.append(result)

            # 출력
            print(f"{result['index']}. {result['title']}")
            print(f"   URL: {validated_url or '❌ 없음'}")
            if validated_url:
                status = "⚠️ 홈페이지" if is_homepage else "✅ 기사"
                print(f"   └─ {status}: {reason}")
            print()

        # 통계
        total = len(results)
        homepage_count = sum(1 for r in results if r['is_homepage'])
        valid_count = total - homepage_count

        print("📊 통계:")
        print(f"   전체: {total}개")
        print(f"   ✅ 유효한 기사 URL: {valid_count}개")
        print(f"   ⚠️ 홈페이지 URL: {homepage_count}개")

        return results

    except Exception as e:
        print(f"❌ The Verge 테스트 오류: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_url_accessibility(url, timeout=5):
    """URL이 실제로 접근 가능한지 테스트 (HTTP HEAD 요청)"""
    try:
        response = requests.head(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }, timeout=timeout, allow_redirects=True)

        # 최종 URL (리다이렉트 후)
        final_url = response.url

        # 상태 코드
        status_code = response.status_code

        # 성공 여부
        is_accessible = (200 <= status_code < 400)

        return {
            'accessible': is_accessible,
            'status_code': status_code,
            'final_url': final_url,
            'redirected': (final_url != url)
        }

    except Exception as e:
        return {
            'accessible': False,
            'status_code': None,
            'final_url': None,
            'redirected': False,
            'error': str(e)
        }

def main():
    """메인 테스트 함수"""

    print("\n" + "="*70)
    print("🔍 뉴스 URL 검증 테스트")
    print("="*70)
    print("목적: 뉴스 URL이 홈페이지가 아닌 실제 기사로 연결되는지 확인")
    print("="*70)

    # Google News 테스트
    google_results = test_google_news_urls(query="6G wireless communication", num_results=5)

    # The Verge 테스트
    verge_results = test_verge_urls(query="wireless", num_results=5)

    # 종합 결과
    print("\n" + "="*70)
    print("📋 종합 결과")
    print("="*70)

    # Google News 문제점
    google_homepage_count = sum(1 for r in google_results if r['is_homepage_source'])
    if google_homepage_count > 0:
        print(f"\n⚠️ Google News 문제점:")
        print(f"   {google_homepage_count}/{len(google_results)}개 URL이 홈페이지로 연결됨")
        print(f"   해결 방법: <source url='...'> 태그 대신 다른 방법 시도 필요")
    else:
        print(f"\n✅ Google News: {len(google_results)}개 URL 모두 정상")

    # The Verge 문제점
    verge_homepage_count = sum(1 for r in verge_results if r['is_homepage'])
    if verge_homepage_count > 0:
        print(f"\n⚠️ The Verge 문제점:")
        print(f"   {verge_homepage_count}/{len(verge_results)}개 URL이 홈페이지로 연결됨")
        print(f"   해결 방법: <link> 태그 추출 방식 재검토 필요")
    else:
        print(f"\n✅ The Verge: {len(verge_results)}개 URL 모두 정상")

    # 추가 테스트: 실제 접근성 확인 (샘플 3개)
    print("\n" + "="*70)
    print("🌐 URL 접근성 테스트 (샘플)")
    print("="*70)

    sample_urls = []
    if google_results:
        sample_urls.extend([r['source_url'] for r in google_results[:2] if r['source_url']])
    if verge_results:
        sample_urls.extend([r['url'] for r in verge_results[:2] if r['url']])

    for i, url in enumerate(sample_urls[:3], 1):
        print(f"\n{i}. 테스트 중: {url[:60]}...")
        access_info = test_url_accessibility(url, timeout=5)

        if access_info['accessible']:
            print(f"   ✅ 접근 가능 (HTTP {access_info['status_code']})")
            if access_info['redirected']:
                print(f"   🔄 리다이렉트됨:")
                print(f"      → {access_info['final_url'][:70]}...")
        else:
            print(f"   ❌ 접근 실패")
            if access_info.get('error'):
                print(f"      오류: {access_info['error']}")

    print("\n" + "="*70)
    print("✅ 테스트 완료")
    print("="*70)

if __name__ == "__main__":
    main()
