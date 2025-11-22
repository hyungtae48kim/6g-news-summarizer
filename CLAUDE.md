# CLAUDE.md - AI Assistant Guide for 6G News Summarizer

## Project Overview

This is a 6G technology news aggregation and summarization application that uses Anthropic Claude AI to search for the latest 6G news, summarize them in Korean, and distribute via email. The project has two main components:

1. **React Frontend** - Interactive web UI for manual news searches
2. **Python Script** - Automated daily email newsletter via GitHub Actions

## Architecture

```
6g-news-summarizer/
├── src/
│   └── App.jsx              # Main React component with Anthropic API integration
├── scripts/
│   └── fetch_and_email.py   # Python automation script for daily newsletters
├── .github/workflows/
│   └── daily-6g-news.yml    # GitHub Actions workflow (runs daily at 9 AM KST)
├── package.json             # Node.js dependencies
└── README.md                # Project documentation (Korean)
```

## Tech Stack

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Lucide React** - Icons

### Backend/Automation
- **Python 3.11** - Automation scripts
- **Anthropic SDK** - Claude AI integration
- **Gmail SMTP** - Email delivery

### AI Integration
- **Model**: `claude-sonnet-4-20250514`
- **Tool**: `web_search_20250305` for real-time news search
- **Output**: JSON with top 5 news items (title, summary in Korean, significance, date, URL)

## Development Commands

```bash
# Install frontend dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run Python script manually (requires env vars)
python scripts/fetch_and_email.py
```

## Environment Variables / Secrets

### Required for GitHub Actions
Set these in GitHub repository secrets:

| Secret | Description |
|--------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude |
| `GMAIL_USER` | Gmail address for sending emails |
| `GMAIL_APP_PASSWORD` | Gmail app-specific password |
| `RECIPIENT_EMAIL` | Email address to receive newsletters |

### Local Development
The React frontend currently makes direct API calls to Anthropic (requires CORS handling or proxy setup).

## Key Code Patterns

### API Response Format
Both frontend and backend expect this JSON structure from Claude:

```json
{
  "top5": [
    {
      "title": "News title in English",
      "summary": "2-3 sentence summary in Korean",
      "significance": "Why this matters in Korean",
      "date": "Date or timeframe",
      "url": "Source URL"
    }
  ],
  "generatedAt": "YYYY-MM-DD"
}
```

### Error Handling
- Rate limiting (429 errors) - Display retry instructions
- JSON parsing - Strip markdown code blocks before parsing
- API response processing - Iterate through content blocks for text

## Workflow Schedule

The GitHub Actions workflow (`daily-6g-news.yml`) runs:
- **Schedule**: Daily at 00:00 UTC (09:00 KST)
- **Manual trigger**: Available via `workflow_dispatch`

Output artifacts (text files) are retained for 30 days.

## Important Conventions

### Language
- **Code comments**: Korean
- **News summaries**: Korean
- **News titles**: English
- **Documentation**: Korean (README.md)

### Styling
- Gradient theme: Blue (#667eea) to Purple (#764ba2)
- Card-based layout with rounded corners
- Consistent padding and spacing

### API Usage
- Max tokens: 4000
- Single API call combines search + summarization
- Response text extraction handles multiple content blocks

## Development Roadmap

- [x] Phase 1: Basic search and summarization
- [x] Phase 2: GitHub Actions automation with email
- [ ] Phase 3: KakaoTalk/Slack/Discord integration

## Troubleshooting

### Common Issues

1. **Rate limiting (429)**: Wait 1-2 minutes before retrying
2. **JSON parse errors**: Check for markdown backticks in response
3. **Email failures**: Verify Gmail app password is correct
4. **Missing news**: Anthropic web search may have limited results

### File Locations
- Frontend entry: `src/App.jsx`
- Automation script: `scripts/fetch_and_email.py`
- Workflow config: `.github/workflows/daily-6g-news.yml`
- Output directory: `output/` (created by Python script)

## Security Notes

- Never commit API keys or credentials
- Use GitHub secrets for all sensitive values
- Gmail requires app-specific password (not regular password)
- Frontend API calls need proper CORS configuration for production
