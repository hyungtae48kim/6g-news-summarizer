import React, { useState } from 'react';
import { Search, Loader2, TrendingUp, Calendar, ExternalLink } from 'lucide-react';

export default function SixGNewsSummarizer() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

  const searchAndSummarize = async () => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      console.log('Starting analysis...');
      
      // 단일 API 호출로 검색과 요약을 한번에 처리
      await delay(500); // 약간의 지연
      
      const apiKey = import.meta.env.VITE_ANTHROPIC_API_KEY;
      if (!apiKey) {
        throw new Error('ANTHROPIC_API_KEY가 설정되지 않았습니다. .env 파일에 VITE_ANTHROPIC_API_KEY를 추가해주세요.');
      }

      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
        },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 4000,
          tools: [{
            type: "web_search_20250305",
            name: "web_search"
          }],
          messages: [{
            role: 'user',
            content: `Search for the latest 6G technology news and developments from 2025. Then analyze and return ONLY a valid JSON object (no markdown, no backticks) with the top 5 most significant news items in this exact structure:

{
  "top5": [
    {
      "title": "News title in English",
      "summary": "2-3 sentence summary in Korean explaining the key points",
      "significance": "Why this matters in Korean",
      "date": "Date or timeframe",
      "url": "Original source URL"
    }
  ],
  "generatedAt": "2025-11-22"
}

Focus on the most recent and impactful 6G developments. Include source URLs when available.`
          }]
        })
      });

      if (!response.ok) {
        if (response.status === 429) {
          throw new Error('요청 한도 초과: 1-2분 후 다시 시도해주세요');
        }
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      console.log('API response:', data);
      
      // Extract text from response
      let responseText = '';
      for (const block of data.content) {
        if (block.type === 'text') {
          responseText += block.text;
        }
      }

      console.log('Response text:', responseText);

      // Parse JSON
      const cleanText = responseText.replace(/```json|```/g, '').trim();
      const parsedResults = JSON.parse(cleanText);
      
      setResults(parsedResults);
      console.log('✅ Success!');
      
    } catch (err) {
      console.error('Error:', err);
      setError('검색 중 오류가 발생했습니다: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-3 rounded-xl">
              <TrendingUp className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-800">6G 기술 뉴스 요약</h1>
              <p className="text-gray-600 mt-1">최신 6G 기술 트렌드를 한눈에</p>
            </div>
          </div>

          <button
            onClick={searchAndSummarize}
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-4 px-6 rounded-xl font-semibold hover:from-blue-700 hover:to-purple-700 transition-all duration-200 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                검색 및 요약 중... (약 10-15초 소요)
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                최신 6G 뉴스 검색하기
              </>
            )}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-6">
            <div className="flex items-start gap-3">
              <div className="bg-red-100 p-2 rounded-lg">
                <span className="text-2xl">⚠️</span>
              </div>
              <div className="flex-1">
                <h3 className="text-red-800 font-semibold mb-2">오류 발생</h3>
                <p className="text-red-700">{error}</p>
                {(error.includes('429') || error.includes('한도')) && (
                  <div className="mt-3 bg-red-100 rounded-lg p-3">
                    <p className="text-sm text-red-800 font-semibold mb-2">💡 해결 방법:</p>
                    <ul className="text-sm text-red-700 space-y-1 list-disc list-inside">
                      <li>1-2분 정도 기다린 후 다시 시도해주세요</li>
                      <li>너무 자주 버튼을 클릭하지 마세요</li>
                      <li>페이지를 새로고침 후 다시 시도해보세요</li>
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {results && (
          <div className="space-y-4">
            <div className="bg-white rounded-xl shadow-lg p-6 mb-4">
              <div className="flex items-center gap-2 text-gray-600">
                <Calendar className="w-5 h-5" />
                <span className="text-sm">생성 시각: {results.generatedAt}</span>
              </div>
            </div>

            {results.top5.map((news, index) => (
              <div
                key={index}
                className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-200"
              >
                <div className="flex items-start gap-4">
                  <div className="bg-gradient-to-br from-blue-600 to-purple-600 text-white w-12 h-12 rounded-xl flex items-center justify-center font-bold text-xl flex-shrink-0">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    {news.url ? (
                      <a 
                        href={news.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-xl font-bold text-blue-600 hover:text-blue-800 mb-2 inline-flex items-center gap-2 hover:underline transition-colors"
                      >
                        {news.title}
                        <ExternalLink className="w-5 h-5" />
                      </a>
                    ) : (
                      <h3 className="text-xl font-bold text-gray-800 mb-2">
                        {news.title}
                      </h3>
                    )}
                    {news.date && (
                      <p className="text-sm text-gray-500 mb-3">{news.date}</p>
                    )}
                    <p className="text-gray-700 mb-3 leading-relaxed">
                      {news.summary}
                    </p>
                    {news.url && (
                      <div className="bg-gray-50 rounded-lg p-3 mb-3 border-l-4 border-gray-400">
                        <p className="text-sm font-semibold text-gray-700 mb-1">📰 출처</p>
                        <a 
                          href={news.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-sm text-blue-600 hover:text-blue-800 hover:underline break-all"
                        >
                          {news.url}
                        </a>
                      </div>
                    )}
                    <div className="bg-blue-50 rounded-lg p-3 border-l-4 border-blue-600">
                      <p className="text-sm font-semibold text-blue-900 mb-1">💡 중요도</p>
                      <p className="text-sm text-blue-800">{news.significance}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {/* Export Options */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6 text-white">
              <h3 className="text-xl font-bold mb-3">📤 다음 단계</h3>
              <div className="space-y-2 text-sm">
                <p>✅ Phase 1: 검색 및 요약 완료</p>
                <p>⏭️ Phase 2: Python 스크립트로 매일 자동 실행</p>
                <p>⏭️ Phase 3: 카카오톡 API 연동</p>
              </div>
              <button
                onClick={() => {
                  const text = results.top5.map((news, i) => 
                    `${i + 1}. ${news.title}\n${news.summary}\n중요도: ${news.significance}\n출처: ${news.url || 'N/A'}\n`
                  ).join('\n');
                  navigator.clipboard.writeText(text);
                  alert('요약본이 클립보드에 복사되었습니다!');
                }}
                className="mt-4 bg-white text-blue-600 px-6 py-2 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
              >
                요약본 복사하기
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}