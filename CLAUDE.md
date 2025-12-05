# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered 6G/RAN technology intelligence system with dynamic keyword extraction and intelligent content selection for RAN SW engineers.

**Workflow**:
1. **Hot Keyword Extraction**: Gemini AI analyzes current trends to generate daily-focused search keywords
2. **Data Collection**: Aggregates 30 items using the hot keyword from multiple sources
3. **Intelligent Selection**: AI selects top 10 items most relevant for RAN SW developers
4. **Deep Analysis**: Provides RAN-focused technical summaries and implementation insights

**Data Sources**:
- **IEEE Xplore**: 10 journal articles (academic research)
- **arXiv**: 10 research papers (preprints)
- **Google News**: 5 news articles (Korean language)
- **The Verge**: 5 tech news articles (English, Atom feed)

**Total**: 30 items collected → Top 10 selected by AI

**Note**: Google Scholar removed due to bot detection (HTTP 429 + CAPTCHA blocking)

**Components**:
- **Frontend**: React SPA for real-time news search with Claude API web search integration
- **Backend**: Python automation script with AI-driven keyword extraction, content selection, and multi-channel distribution (Email + Telegram)

## Commands

### Frontend Development
```bash
npm install              # Install dependencies
npm run dev              # Start Vite dev server (http://localhost:5173)
npm run build            # Production build
npm run preview          # Preview production build
```

### Backend Execution

**Quick Setup with Virtual Environment** (Recommended):
```bash
# One-time setup (creates venv and installs dependencies)
./setup_venv.sh

# Activate virtual environment
source venv/bin/activate

# Run the script
python scripts/fetch_6g_professional.py

# Deactivate when done
deactivate
```

**Manual Setup**:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies from requirements.txt
pip install -r requirements.txt

# Run the script
python scripts/fetch_6g_professional.py
```

**Without Virtual Environment** (Not recommended):
```bash
# Install Python dependencies globally
pip install requests beautifulsoup4 lxml

# Run the script
python3 scripts/fetch_6g_professional.py
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

**Intelligent Pipeline**:

1. **Hot Keyword Extraction** (`extract_hot_keywords()`):
   - Uses Gemini with RAN Network Professor persona
   - Considers current trends: O-RAN, AI/ML in RAN, terahertz, RIS, network slicing
   - Returns focused 3-5 word search query
   - Fallback: "6G wireless communications"

2. **Data Collection** (30 items total):
   - **IEEE Xplore API**: 10 journals (requires `IEEE_API_KEY`)
   - **arXiv API**: 10 research papers
   - **Google News RSS**: 5 news articles (Korean)
   - **The Verge Atom Feed**: 5 tech news articles (English)
   - All sources use the extracted hot keyword
   - **Note**: Google Scholar removed due to bot detection (HTTP 429 + CAPTCHA)

3. **Intelligent Selection** (`select_top_items_for_ran_engineers()`):
   - Gemini analyzes all 30 items with RAN SW Engineer criteria
   - Selection criteria:
     - Practical applicability to RAN software development
     - Novel algorithms/architectures for RAN
     - O-RAN and Open RAN developments
     - AI/ML in RAN optimization
     - PHY layer innovations affecting upper layers
   - Returns top 10 most relevant items

4. **Deep Analysis** (`summarize_with_gemini()`):
   - RAN Network Professor & RAN SW Engineer persona
   - Focus areas:
     - RAN protocol stack (MAC/RLC/PDCP/RRC) impact
     - O-RAN/Open RAN interfaces and architecture
     - AI/ML-based RAN optimization algorithms
     - Real-time performance requirements
     - Implementation considerations
   - Fallback to raw descriptions if API fails

**Output Format**:
- Categorized by type (Journal/Paper/News)
- Each item includes:
  - Title (original English)
  - Summary (Korean, with RAN architecture/algorithm/protocol perspective)
  - Message (Korean, SW implementation insights for RAN developers)
  - URL
  - Type

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
   - Includes hot keyword in report metadata
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

### AI-Driven Workflow
- **Three Gemini API Calls Per Run**:
  1. Hot keyword extraction (~100 tokens)
  2. Top 10 item selection (~200 tokens)
  3. Deep analysis and summarization (~8192 tokens)
- **Total Token Usage**: ~8500 tokens per execution
- **Daily Execution**: Well within free tier limits

### API Rate Limiting
- **Gemini API**: Free tier allows 1,500 requests/month
- **Frontend (Claude API)**: Implements 429 error handling with user guidance to wait 1-2 minutes
- **IEEE API**: Authentication errors (403) are caught and logged

### Error Resilience
- Hot keyword extraction failure → fallback to "6G wireless communications"
- Item selection failure → uses first 10 items from collection
- Script continues with partial data if any source fails
- Gemini parsing errors trigger fallback to raw descriptions
- Missing IEEE API key skips journal collection but continues
- Missing Telegram credentials silently skip notification (not fatal)

### JSON Parsing Error Handling
- **Issue**: Gemini responses may contain unescaped special characters causing JSON parsing failures
- **Solution**: Enhanced prompt explicitly instructs Gemini to escape special characters and avoid line breaks
- **Debugging**: On JSON parse error, the script:
  - Outputs error position (line, column)
  - Displays 400-character context around the error
  - Saves full response to `debug_gemini_response_YYYYMMDD_HHMMSS.txt` for inspection
  - Falls back to `create_summary_without_ai()` with raw descriptions

### Web Scraping Challenges
- **Google Scholar removed**: Bot detection (HTTP 429 + CAPTCHA) prevents reliable scraping
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

1. **Dynamic Content Selection**: Unlike static keyword systems, this uses AI to:
   - Extract daily-relevant search keywords
   - Collect 30 items from reliable sources (IEEE, arXiv, Google News)
   - Intelligently select top 10 for RAN SW engineers
   - Result: Higher quality, more relevant content daily

2. **RAN-Focused Persona**: Uses dual persona approach:
   - RAN Network Professor (theoretical depth)
   - RAN SW Engineer (practical implementation)
   - Focus on O-RAN, protocol stack, AI/ML, real-time optimization

3. **Frontend Security Issue**: Claude API key is exposed in browser requests. For production, implement backend proxy.

4. **IEEE API Dependency**: Script requires valid IEEE API key. Will skip IEEE journals if key is missing/invalid but continues with other sources.

5. **Bilingual Output**: All summaries/insights are in Korean with RAN-specific technical details, but titles remain in original English. This is intentional for the target audience.

6. **AI Prompt Engineering**:
   - Hot keyword: RAN-focused trend analysis with current year context
   - Selection: Practical RAN SW development criteria
   - Summarization: RAN protocol stack and implementation perspective

7. **File Artifacts**:
   - GitHub Actions saves to `output/` directory
   - 90-day retention for markdown reports
   - Report includes hot keyword metadata

8. **Multiple Email Templates**: Script contains three different HTML email template functions. Currently uses `create_email_safe_html()` for maximum compatibility.

9. **Cost**: Entire system operates on free tiers (Gemini Free API with ~8500 tokens/day, IEEE API free tier, GitHub Actions free minutes, Gmail SMTP, Telegram Bot API).
