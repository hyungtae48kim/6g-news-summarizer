# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered 6G technology intelligence system that aggregates and summarizes news from multiple academic and industry sources.

**Data Sources**:
- IEEE Xplore journals (5 items)
- arXiv papers (3 items)
- Google Scholar papers (2 items)
- Google News articles (5 items)

**Components**:
- **Frontend**: React SPA for real-time news search with Claude API web search integration
- **Backend**: Python automation script for scheduled news fetching, AI summarization, and multi-channel distribution (Email + Telegram)

## Commands

### Frontend Development
```bash
npm install              # Install dependencies
npm run dev              # Start Vite dev server (http://localhost:5173)
npm run build            # Production build
npm run preview          # Preview production build
```

### Backend Execution
```bash
# Run the professional intelligence script
python scripts/fetch_6g_professional.py

# Install Python dependencies
pip install requests beautifulsoup4 lxml
```

### GitHub Actions
- Workflow: `.github/workflows/daily-6g-professional.yml`
- Runs daily at 00:00 UTC (09:00 KST)
- Supports manual trigger via `workflow_dispatch`

## Architecture

### Frontend Architecture ([src/App.jsx](src/App.jsx))

**Single-page React application** that performs browser-based API calls:

1. **Direct Claude API Integration**:
   - Calls `https://api.anthropic.com/v1/messages` directly from browser (NOT proxied)
   - Uses Claude Sonnet 4 (`claude-sonnet-4-20250514`) with `web_search_20250305` tool
   - API key must be provided by user or environment (security concern for production)

2. **Response Flow**:
   ```
   User clicks → Claude API call with web_search tool → Parse JSON response → Display top 5 news
   ```

3. **Error Handling**: Displays user-friendly errors for rate limiting (429) and API failures

4. **Output Format**: Bilingual cards with English titles, Korean summaries/insights, clickable source URLs

### Backend Architecture

**Main Script** ([scripts/fetch_6g_professional.py](scripts/fetch_6g_professional.py))

**Data Collection Pipeline** (15 items total):
1. IEEE Xplore API: 5 journals (requires `IEEE_API_KEY`)
2. arXiv API: 3 papers
3. Google Scholar scraping: 2 papers
4. Google News RSS: 5 news articles

**AI Analysis**:
- Uses Gemini 2.5 Flash API with "6G Technology Research Engineer" persona
- Generates technical summaries and practical insights
- Fallback to raw descriptions if API fails

**Output Format**:
- Categorized by type (Journal/Paper/News)
- Each item includes: title, summary (Korean), engineer's message (Korean), URL, type

#### Distribution Channels

1. **Email (Gmail SMTP)**:
   - HTML email with gradient design, card-based layout
   - Color-coded sections (blue=Journal, green=Paper, orange=News)
   - Table-based layout for email client compatibility
   - Requires Gmail app-specific password (NOT regular password)

2. **Telegram Bot**:
   - Markdown-formatted messages with inline link buttons
   - Truncated to 4096 character limit
   - Disables web preview for cleaner appearance
   - Optional (skipped if credentials missing)

3. **File Storage**:
   - Saves to `output/6g_report_YYYY-MM-DD.md` (Markdown format)
   - Uploaded as GitHub Actions artifact (90-day retention)

### Data Structure

**Backend Output Format**:
```json
{
  "summaries": [
    {
      "title": "Article/paper title",
      "summary": "3-4 sentence Korean technical summary",
      "message": "Engineer-focused practical implications (Korean)",
      "url": "Source URL",
      "type": "Journal|Paper|News"
    }
  ],
  "generatedAt": "YYYY-MM-DD"
}
```

**Frontend Output Format** (Claude API):
```json
{
  "top5": [
    {
      "title": "English news title",
      "summary": "2-3 sentence Korean summary",
      "significance": "Why this matters (Korean)",
      "date": "Publication date",
      "url": "Source URL"
    }
  ],
  "generatedAt": "YYYY-MM-DD"
}
```

## Environment Variables

| Variable | Required For | Description |
|----------|-------------|-------------|
| `GEMINI_API_KEY` | Backend | Google Gemini API key from AI Studio |
| `IEEE_API_KEY` | Backend | IEEE Xplore API key (developer.ieee.org) |
| `GMAIL_USER` | Email sending | Gmail address (sender) |
| `GMAIL_APP_PASSWORD` | Email sending | 16-char app-specific password |
| `RECIPIENT_EMAIL` | Email sending | Recipient email address |
| `TELEGRAM_BOT_TOKEN` | Telegram (optional) | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Telegram (optional) | Chat ID from @userinfobot |
| `ANTHROPIC_API_KEY` | Frontend only | Claude API key for web search |

## Key Implementation Details

### API Rate Limiting
- **Gemini API**: Free tier allows 1,500 requests/month
- **Frontend (Claude API)**: Implements 429 error handling with user guidance to wait 1-2 minutes
- **IEEE API**: Authentication errors (403) are caught and logged

### Error Resilience
- Script continues with partial data if any source fails
- Gemini parsing errors trigger fallback to raw descriptions
- Missing IEEE API key skips journal collection but continues
- Missing Telegram credentials silently skip notification (not fatal)

### Web Scraping Challenges
- Google Scholar scraping may be unstable (relies on HTML structure)
- All HTTP requests use `User-Agent` header to avoid bot detection
- BeautifulSoup with `lxml` parser for RSS, `html.parser` for HTML

### Email HTML Compatibility
- Uses table-based layout (not CSS Grid/Flexbox) for email client compatibility
- Inline styles only (no external CSS or CSS variables)
- Gradient backgrounds in header for visual appeal
- Three email template functions available: `create_html_email()`, `create_visual_html_email()`, `create_email_safe_html()` (currently using the last one)

### Telegram Message Formatting
- Uses Markdown parse mode with escaped special characters (`_`, `*`, `[`)
- Truncates content to fit 4096 character limit
- Disables web preview for cleaner appearance
- Groups items by type with section headers and statistics

## Testing Workflows

**Manual GitHub Actions Test**:
1. Go to Actions tab
2. Select "Daily 6G Professional Report" workflow
3. Click "Run workflow" → "Run workflow"
4. Check email/Telegram for results
5. Download artifacts from workflow run summary

**Local Testing**:
```bash
# Set environment variables
export GEMINI_API_KEY="your_key"
export IEEE_API_KEY="your_ieee_key"
export GMAIL_USER="your@gmail.com"
export GMAIL_APP_PASSWORD="your_app_password"
export RECIPIENT_EMAIL="recipient@example.com"

# Optional Telegram
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Run script
python scripts/fetch_6g_professional.py
```

## Important Notes for Development

1. **Frontend Security Issue**: Claude API key is exposed in browser requests. For production, implement backend proxy.

2. **IEEE API Dependency**: Script requires valid IEEE API key. Will skip IEEE journals if key is missing/invalid but continues with other sources.

3. **Bilingual Output**: All summaries/insights are in Korean, but titles remain in original English. This is intentional for the target audience.

4. **AI Prompt Engineering**: Uses explicit "6G Technology Research Engineer" persona in Gemini prompt for better technical analysis.

5. **File Artifacts**:
   - GitHub Actions saves to `output/` directory
   - 90-day retention for markdown reports

6. **Multiple Email Templates**: Script contains three different HTML email template functions. Currently uses `create_email_safe_html()` for maximum compatibility.

7. **Cost**: Entire system operates on free tiers (Gemini Free API, IEEE API free tier, GitHub Actions free minutes, Gmail SMTP, Telegram Bot API).
