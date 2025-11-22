# CLAUDE.md - 6G News Summarizer

## Project Overview

AI-powered application that searches for latest 6G technology news and provides Korean-language summaries. Has two components:
- **Frontend:** React web app for real-time search and summarization
- **Backend:** Python scripts for scheduled news fetching and email notifications

## Project Structure

```
6g-news-summarizer/
├── .github/workflows/
│   ├── daily-6g-news.yml         # GitHub Actions for Claude API
│   └── daily-6g-news-gemini.yml  # GitHub Actions for Gemini API
├── src/
│   └── App.jsx                   # Main React component
├── scripts/
│   ├── fetch_and_email.py        # Python script (Claude API)
│   └── fetch_and_email_gemini.py # Python script (Gemini API)
├── output/                       # Generated news summaries
├── README.md
└── package.json
```

## Tech Stack

### Frontend
- React 18.2.0
- Vite 4.4.5
- Tailwind CSS 3.3.3
- Lucide React (icons)

### Backend
- Python 3.11
- anthropic (Claude API client)
- requests, beautifulsoup4, lxml
- smtplib (Gmail SMTP)

## How to Run

### Frontend
```bash
npm install
npm run dev      # Development server
npm run build    # Production build
```

### Backend Scripts
```bash
# Claude version
python scripts/fetch_and_email.py

# Gemini version
python scripts/fetch_and_email_gemini.py
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Claude API key (for fetch_and_email.py) |
| `GEMINI_API_KEY` | Google Gemini API key (for fetch_and_email_gemini.py) |
| `GMAIL_USER` | Gmail sender address |
| `GMAIL_APP_PASSWORD` | Gmail app-specific password |
| `RECIPIENT_EMAIL` | Email recipient address |

## API Details

### Claude API
- Model: `claude-sonnet-4-20250514`
- Endpoint: `https://api.anthropic.com/v1/messages`
- Uses web_search tool for real-time news

### Gemini API
- Model: `gemini-2.5-flash`
- Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`
- Uses Google News RSS for initial search

## Data Structure

```json
{
  "top5": [
    {
      "title": "News title (English)",
      "summary": "2-3 sentence summary (Korean)",
      "significance": "Why this matters (Korean)",
      "date": "Date or timeframe",
      "url": "Source URL"
    }
  ],
  "generatedAt": "YYYY-MM-DD"
}
```

## Key Functions

### App.jsx
- `searchAndSummarize()` - Calls Claude API with web search, updates state with results

### fetch_and_email.py
- `fetch_6g_news()` - Calls Claude API for news search/summarization
- `create_html_email(news_data)` - Generates HTML email template
- `send_email(news_data)` - Sends via Gmail SMTP
- `save_to_file(news_data)` - Saves to output/ directory

### fetch_and_email_gemini.py
- `search_google_news(query, num_results)` - Scrapes Google News RSS
- `fetch_6g_news_with_gemini()` - Uses Gemini to analyze and rank news
- `create_summary_from_news(news_items)` - Fallback without AI
- Same email/save functions as Claude version

## GitHub Actions

Both workflows run daily at 00:00 UTC (09:00 KST):
- `daily-6g-news.yml` - Uses Claude API
- `daily-6g-news-gemini.yml` - Uses Gemini API

Artifacts saved to output/*.txt for 30 days.

## Development Notes

- Frontend directly calls Claude API from browser (should proxy through backend in production)
- Rate limiting: Handle 429 errors, wait 1-2 minutes between requests
- Email requires Gmail app-specific password (not account password)
- Outputs are bilingual: English titles, Korean summaries
