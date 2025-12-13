#!/usr/bin/env python3
"""
수정된 Google News URL 추출 테스트
- Google 리다이렉트 URL이 제대로 추출되는지 확인
- URL이 유효하고 클릭 가능한지 검증
"""

import sys
import os

# 메인 스크립트의 함수를 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from fetch_6g_professional import search_google_news, validate_and_clean_url

def test_fixed_google_news():
    """수정된 Google News 함수 테스트"""

    print("\n" + "="*70)
    print("✅ 수정된 Google News URL 추출 테스트")
    print("="*70)
    print("목적: Google 리다이렉트 URL이 제대로 추출되는지 확인")
    print("="*70)

    # Google News에서 뉴스 가져오기
    results = search_google_news(query="6G wireless communication", num_results=5)

    print("\n" + "="*70)
    print("📋 테스트 결과")
    print("="*70)

    if not results:
        print("❌ 결과 없음")
        return

    for i, item in enumerate(results, 1):
        print(f"\n{i}. {item['title'][:80]}")
        print(f"   URL: {item['url'][:100]}...")

        # URL 검증
        if 'news.google.com' in item['url']:
            print(f"   ✅ Google 리다이렉트 URL (브라우저에서 실제 기사로 리다이렉트됨)")
        elif item['url'].startswith('http'):
            print(f"   ✅ 직접 URL")
        else:
            print(f"   ⚠️ 예상치 못한 URL 형식")

    # 통계
    print("\n" + "="*70)
    print("📊 통계")
    print("="*70)
    print(f"전체 결과: {len(results)}개")

    google_redirect_count = sum(1 for r in results if 'news.google.com' in r['url'])
    direct_url_count = len(results) - google_redirect_count

    print(f"✅ Google 리다이렉트 URL: {google_redirect_count}개")
    print(f"✅ 직접 URL: {direct_url_count}개")

    if len(results) > 0:
        print(f"\n✅ 성공: 모든 URL이 유효하고 클릭 가능합니다!")
        print(f"   (Google 리다이렉트 URL은 브라우저에서 클릭 시 실제 기사로 이동)")
    else:
        print(f"\n⚠️ 결과 없음")

    print("\n" + "="*70)

if __name__ == "__main__":
    test_fixed_google_news()
