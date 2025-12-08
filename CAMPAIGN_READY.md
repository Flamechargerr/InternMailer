# 🚀 Full Campaign - Ready to Launch!

## Setup Complete ✅

Your AI-powered email system is ready to send personalized emails to all 379 European professors!

## How to Run

```bash
python campaign_sender.py
```

When prompted:
- Enter `10` for a small test batch
- Enter `50` for medium batch  
- Enter `all` for all 379 professors

## What It Does

For each professor:
1. 📚 Fetches their real research papers (Semantic Scholar)
2. 🤖 Generates unique AI content (Llama 3)
3. 📧 Sends personalized email
4. ⏳ Waits 10 seconds (rate limiting)

## Timing

- **Per email**: ~3 minutes (fetch + AI + send)
- **50 emails**: ~2.5 hours
- **All 379**: ~19 hours

## Features

✅ Real research papers from Semantic Scholar
✅ AI-generated unique content (Llama 3)
✅ Mentions specific paper titles
✅ Professional formatting  
✅ CV auto-attached
✅ Rate limited (10 sec between emails)
✅ Progress tracking
✅ Statistics at end

## Safety

- 10-second delays prevent spam detection
- Fallback to generic if papers not found
- Error handling for failed sends
- Can cancel anytime with Ctrl+C

## Example Command

```bash
python campaign_sender.py
# Enter: 10
# Sends to first 10 professors
```

Ready to launch! 🚀
