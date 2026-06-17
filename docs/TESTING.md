# Comprehensive Testing Guide

## Quick Test

Run the comprehensive test suite:

```bash
# Test with auto-starting server
python3 run_comprehensive_test.py

# Test existing server
python3 run_comprehensive_test.py --no-start

# Test different URL
python3 run_comprehensive_test.py --url http://your-server:port
```

## Manual Testing

### 1. Start Server

```bash
python3 main.py
```

### 2. Test Endpoints

```bash
# Health check
curl http://localhost:5050/health

# Metrics
curl http://localhost:5050/metrics

# Stats
curl http://localhost:5050/api/stats

# Available contacts
curl http://localhost:5050/api/contacts/available

# Preview emails
curl http://localhost:5050/preview-emails?count=1

# Jobs
curl http://localhost:5050/api/jobs

# Daemon status
curl http://localhost:5050/api/daemon/status
```

### 3. Test Pages

Open in browser:
- http://localhost:5050/ - Dashboard
- http://localhost:5050/jobs - Jobs page
- http://localhost:5050/contacts - Contacts page
- http://localhost:5050/replies - Replies page
- http://localhost:5050/settings - Settings page

### 4. Test POST Endpoints

```bash
# Send emails (requires valid data)
curl -X POST http://localhost:5050/send-emails \
  -H "Content-Type: application/json" \
  -d '{"count": 1}'

# AI Cover Letter
curl -X POST http://localhost:5050/api/ai/cover-letter \
  -H "Content-Type: application/json" \
  -d '{"role": "Software Engineer", "company": "Test Corp", "skills": "Python"}'

# AI Interview Guide
curl -X POST http://localhost:5050/api/ai/interview-guide \
  -H "Content-Type: application/json" \
  -d '{"role": "Software Engineer", "company": "Test Corp", "skills": "Python"}'
```

## Browser Testing

### Using Playwright (if installed)

```bash
# Install Playwright
pip install playwright
playwright install

# Run browser tests
python3 tests/test_browser_comprehensive.py
```

### Manual Browser Testing

1. Open http://localhost:5050
2. Check all buttons are clickable
3. Test all navigation links
4. Test form submissions
5. Check for JavaScript errors (F12 Console)
6. Test responsive design (mobile/tablet)

## Test Checklist

### Endpoints
- [ ] `/health` returns 200
- [ ] `/metrics` returns 200
- [ ] `/api/stats` returns 200
- [ ] `/api/contacts/available` returns 200
- [ ] `/preview-emails` returns 200
- [ ] `/api/jobs` returns 200
- [ ] `/api/daemon/status` returns 200

### Pages
- [ ] `/` loads correctly
- [ ] `/jobs` loads correctly
- [ ] `/contacts` loads correctly
- [ ] `/replies` loads correctly
- [ ] `/settings` loads correctly

### Buttons & UI
- [ ] All buttons are clickable
- [ ] Navigation works
- [ ] Forms submit correctly
- [ ] No JavaScript errors
- [ ] Responsive design works

### API Functionality
- [ ] Email sending works (if configured)
- [ ] Job discovery works
- [ ] AI endpoints work (if API key configured)
- [ ] Rate limiting works
- [ ] Error handling works

## Expected Results

### Success Criteria
- ✅ 80%+ endpoints return 200
- ✅ All pages load without errors
- ✅ No critical JavaScript errors
- ✅ Forms submit successfully
- ✅ Rate limiting prevents abuse

### Common Issues

1. **Server not running**
   - Start with: `python3 main.py`
   - Check port 5050 is available

2. **Connection refused**
   - Server may not be started
   - Check firewall settings
   - Verify URL is correct

3. **500 errors**
   - Check server logs
   - Verify configuration
   - Check database files exist

4. **Rate limit errors**
   - Normal behavior for testing
   - Wait 60 seconds and retry
   - Adjust rate limits if needed

## Test Results

Test results are saved to:
- `comprehensive_test_results.json` - Full test results
- `endpoint_test_results.json` - Endpoint-only results

Review these files for detailed information about what passed/failed.
