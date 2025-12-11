#!/usr/bin/env python3
"""
URL 보존 로직 테스트
"""

# 테스트용 헬퍼 함수 복사
def _preserve_original_urls(summaries, original_items):
    """
    Gemini 응답에서 URL이 잘못되었을 경우 원본 아이템의 URL을 복원

    Args:
        summaries: Gemini가 반환한 요약 결과 리스트
        original_items: 원본 아이템 리스트
    """
    # 원본 아이템을 title로 매핑
    original_map = {}
    for item in original_items:
        # title을 정규화 (공백, 특수문자 제거)
        normalized_title = item['title'].lower().strip()
        original_map[normalized_title] = item['url']

    # 각 요약 아이템의 URL을 원본에서 복원
    for summary in summaries:
        summary_title = summary.get('title', '').lower().strip()

        # 정확히 일치하는 title 찾기
        if summary_title in original_map:
            summary['url'] = original_map[summary_title]
            continue

        # 부분 일치 시도 (title이 일부만 포함된 경우)
        for orig_title, orig_url in original_map.items():
            # 양방향 부분 일치 확인
            if (summary_title in orig_title or orig_title in summary_title) and len(summary_title) > 20:
                summary['url'] = orig_url
                break

# 테스트 데이터
original_items = [
    {
        'title': 'SKT, AI 인프라 로드맵 발표 "국가대표 AI 사업자로서 AI 인프라 진화 이끌 것"',
        'url': 'https://news.sktelecom.com/actual-article-url-1',
        'type': 'News'
    },
    {
        'title': '삼성+SK+현대차그룹, 엔비디아와 손잡고 한국형 피지컬 AI 혁명 나선다',
        'url': 'http://www.netzeronews.kr/actual-article-url-2',
        'type': 'News'
    },
    {
        'title': "'NVIDIA Aerial' 확장이 불러올 통신 분야의 혁신",
        'url': 'https://blogs.nvidia.co.kr/actual-article-url-3',
        'type': 'News'
    }
]

# Gemini가 잘못된 URL로 반환한 요약 (대표 URL만 반환)
summaries = [
    {
        'title': 'SKT, AI 인프라 로드맵 발표 "국가대표 AI 사업자로서 AI 인프라 진화 이끌 것"',
        'url': 'https://news.sktelecom.com',  # 잘못된 대표 URL
        'summary': '테스트 요약 1',
        'message': '테스트 메시지 1',
        'type': 'News'
    },
    {
        'title': '삼성+SK+현대차그룹, 엔비디아와 손잡고 한국형 피지컬 AI 혁명 나선다',
        'url': 'http://www.netzeronews.kr',  # 잘못된 대표 URL
        'summary': '테스트 요약 2',
        'message': '테스트 메시지 2',
        'type': 'News'
    },
    {
        'title': "'NVIDIA Aerial' 확장이 불러올 통신 분야의 혁신",
        'url': 'https://blogs.nvidia.co.kr',  # 잘못된 대표 URL
        'summary': '테스트 요약 3',
        'message': '테스트 메시지 3',
        'type': 'News'
    }
]

print("="*70)
print("URL 보존 로직 테스트")
print("="*70)

print("\n[Before] 잘못된 URL:")
for i, summary in enumerate(summaries, 1):
    print(f"{i}. {summary['title'][:50]}...")
    print(f"   URL: {summary['url']}")

# URL 복원 함수 실행
_preserve_original_urls(summaries, original_items)

print("\n[After] 복원된 URL:")
for i, summary in enumerate(summaries, 1):
    print(f"{i}. {summary['title'][:50]}...")
    print(f"   URL: {summary['url']}")

# 검증
print("\n" + "="*70)
print("검증 결과:")
print("="*70)
all_correct = True
for i, (summary, original) in enumerate(zip(summaries, original_items), 1):
    if summary['url'] == original['url']:
        print(f"✅ {i}번 아이템: URL 복원 성공")
    else:
        print(f"❌ {i}번 아이템: URL 복원 실패")
        print(f"   기대: {original['url']}")
        print(f"   실제: {summary['url']}")
        all_correct = False

if all_correct:
    print("\n✅ 모든 URL이 정확히 복원되었습니다!")
else:
    print("\n❌ 일부 URL 복원에 실패했습니다.")
