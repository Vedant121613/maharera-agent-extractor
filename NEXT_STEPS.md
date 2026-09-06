# Next Steps - MahaRERA Agent Extractor

## ✅ What We've Done

### 1. **Improved Parallel Scraper Stability**
- Enhanced error handling and recovery mechanisms
- Added automatic page recreation when browsers close unexpectedly
- Improved browser context management to prevent premature closures
- Added per-page error handling with graceful recovery
- Explicit cleanup in finally blocks to prevent resource leaks

### 2. **Added Monitoring & Utility Scripts**
- `captcha_stats.py` - Analyze CAPTCHA solving statistics
- `check_db.py` - Quick database statistics viewer
- `check_failed.py` - List all failed agents for retry
- `check_recent.py` - View recently collected agents
- `monitor_live.py` - Real-time monitoring of scraping progress

### 3. **Fixed .gitignore**
- Properly excludes data files (*.db, data/)
- Excludes logs and temporary files
- Keeps utility scripts tracked in git
- Protects sensitive files (.env, *.pem, *.ppk)

### 4. **Pushed to GitHub**
- All changes committed and pushed successfully
- Commit: `7e0d479` - "Improve parallel scraper stability and add monitoring utilities"

---

## 🚀 What To Do Next

### Option 1: **Run Parallel Scraper (Recommended)**
The parallel scraper is now more stable and can handle browser closures gracefully.

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run with 3 workers for 100 pages
python parallel_scraper.py --workers 3 --start-page 1 --pages 100

# Or run with visible browsers for debugging
python parallel_scraper.py --workers 2 --start-page 1 --pages 50 --no-headless

# Export to Excel after scraping
python parallel_scraper.py --workers 3 --start-page 1 --pages 100 --export
```

**Recommended settings:**
- Start with 2-3 workers to test stability
- Use headless mode for faster performance
- Monitor with `python monitor_live.py` in another terminal

### Option 2: **Test Single-Threaded Scraper**
If you still experience issues, use the stable single-threaded version:

```bash
python main.py --start-page 1 --pages 50
```

### Option 3: **Continue From Where You Left Off**
Check which pages have been completed:

```bash
# Check database status
python check_db.py

# Check recent collections
python check_recent.py

# Check failed agents
python check_failed.py

# Then resume from the next page
python parallel_scraper.py --workers 3 --start-page <NEXT_PAGE> --pages 100
```

### Option 4: **Retry Failed Agents**
After bulk scraping, retry failed agents:

```bash
# Retry all failed agents
python scripts/retry_failed.py --max-retries 3

# Check stats
python captcha_stats.py
```

---

## 📊 Monitor Progress

### Real-time Monitoring (In Separate Terminal)
```bash
python monitor_live.py
```

### Quick Stats
```bash
python check_db.py
```

### CAPTCHA Analysis
```bash
python captcha_stats.py
```

---

## 🔧 Troubleshooting

### If Browsers Keep Closing:
1. **Reduce worker count** - Try `--workers 1` or `--workers 2`
2. **Use visible mode** - Add `--no-headless` to see what's happening
3. **Check memory** - Close other applications
4. **Update Playwright** - Run `pip install --upgrade playwright; playwright install chromium`

### If CAPTCHA Keeps Failing:
1. **Use manual solver** - Set `CAPTCHA_STRATEGY=manual` in `.env`
2. **Reduce speed** - Increase delays in `config/config.py`
3. **Check CAPTCHA stats** - Run `python captcha_stats.py`

### If Database Errors:
1. **Check database** - Run `python check_db.py`
2. **Backup database** - Copy `data/agents.db` before retrying
3. **Clean duplicates** - Run `python scripts/cleanup.py`

---

## 📦 Export Results

### Export to Excel:
```bash
# Export all collected agents
python -c "from exporter.excel import ExcelExporter; from database.database import Database; from config.config import Config; ExcelExporter(Database(Config.DB_PATH)).export()"

# Or use the --export flag with parallel scraper
python parallel_scraper.py --workers 3 --pages 100 --export
```

---

## 🎯 Recommended Workflow

### For Large-Scale Scraping (1000+ pages):

```bash
# 1. Start monitoring in one terminal
python monitor_live.py

# 2. In another terminal, run parallel scraper
python parallel_scraper.py --workers 3 --start-page 1 --pages 500

# 3. After completion, retry failed
python scripts/retry_failed.py --max-retries 2

# 4. Export results
python -c "from exporter.excel import ExcelExporter; from database.database import Database; from config.config import Config; print(ExcelExporter(Database(Config.DB_PATH)).export())"

# 5. Check final stats
python check_db.py
python captcha_stats.py
```

### For Testing/Small Batches:

```bash
# Test with visible browsers first
python parallel_scraper.py --workers 1 --start-page 1 --pages 5 --no-headless

# If successful, scale up
python parallel_scraper.py --workers 3 --start-page 6 --pages 50
```

---

## 📝 Key Improvements in This Update

1. **Browser Stability**
   - Pages are now checked before use (`is_closed()`)
   - Automatic page recreation on closure
   - Better cleanup in finally blocks

2. **Error Recovery**
   - Per-page try-catch blocks
   - Worker continues even if one page fails
   - Graceful degradation instead of crashing

3. **Resource Management**
   - Explicit browser context management
   - Proper cleanup of all resources
   - Thread-safe statistics tracking

4. **Monitoring Tools**
   - Real-time progress monitoring
   - Database inspection utilities
   - CAPTCHA performance analysis

---

## 🔐 Before Running at Scale

1. **Check .env file** - Ensure API keys are set if using API-based CAPTCHA
2. **Test small batch** - Always test with 5-10 pages first
3. **Backup database** - Copy `data/agents.db` before large runs
4. **Monitor resources** - Watch CPU/memory usage
5. **Use headless mode** - Faster and more stable for production

---

## 📞 Need Help?

- Check logs in `logs/extractor.log`
- Run `python check_failed.py` to see error details
- Use `--no-headless` to watch browser behavior
- Reduce `--workers` if experiencing instability

---

**Current Status:** ✅ Ready for production scraping with improved stability
**GitHub:** ✅ All changes pushed to main branch
**Next Action:** Run parallel scraper or test with small batch

Good luck with your scraping! 🚀
