# 🚀 Quick Start Guide

## Prerequisites
- Python 3.10+ installed
- Virtual environment activated
- Playwright installed

## 30-Second Setup

```powershell
# 1. Activate environment
.\venv\Scripts\Activate.ps1

# 2. Verify setup
python check_db.py

# 3. Run scraper
python parallel_scraper.py --workers 2 --start-page 1 --pages 10
```

## Basic Commands

### Single-Page Test
```bash
python main.py --start-page 1 --pages 1
```

### Small Batch (10 pages, 2 workers)
```bash
python parallel_scraper.py --workers 2 --start-page 1 --pages 10
```

### Medium Batch (50 pages, 3 workers)
```bash
python parallel_scraper.py --workers 3 --start-page 1 --pages 50
```

### Large Batch (100 pages, 3 workers)
```bash
python parallel_scraper.py --workers 3 --start-page 1 --pages 100 --export
```

### With Visible Browsers (Debug)
```bash
python parallel_scraper.py --workers 1 --start-page 1 --pages 5 --no-headless
```

## Monitoring Commands

### Check Database Stats
```bash
python check_db.py
```

### View Recent Collections
```bash
python check_recent.py
```

### Check Failed Agents
```bash
python check_failed.py
```

### Live Monitoring
```bash
python monitor_live.py
```

### CAPTCHA Statistics
```bash
python captcha_stats.py
```

## Retry Failed Agents

```bash
python scripts/retry_failed.py --max-retries 3
```

## Export to Excel

```bash
# Quick export
python -c "from exporter.excel import ExcelExporter; from database.database import Database; from config.config import Config; print(ExcelExporter(Database(Config.DB_PATH)).export())"

# Or use flag during scraping
python parallel_scraper.py --workers 3 --pages 50 --export
```

## Recommended Workflow

### First Time Use:
```bash
# 1. Test with single page
python main.py --start-page 1 --pages 1

# 2. Test with small batch
python parallel_scraper.py --workers 1 --start-page 2 --pages 5

# 3. Scale up gradually
python parallel_scraper.py --workers 2 --start-page 7 --pages 20
python parallel_scraper.py --workers 3 --start-page 27 --pages 50
```

### Production Use:
```bash
# Terminal 1: Monitor
python monitor_live.py

# Terminal 2: Scrape
python parallel_scraper.py --workers 3 --start-page 1 --pages 500

# After completion: Retry and Export
python scripts/retry_failed.py
python check_db.py
```

## Troubleshooting

### Browser Crashes
- Reduce workers: `--workers 1`
- Use visible mode: `--no-headless`
- Update Playwright: `pip install --upgrade playwright; playwright install chromium`

### CAPTCHA Issues
- Check strategy in `.env`: `CAPTCHA_STRATEGY=local` or `manual`
- View stats: `python captcha_stats.py`
- Slow down: Increase `REQUEST_DELAY_MIN` in `config/config.py`

### Database Errors
- Check: `python check_db.py`
- Backup: Copy `data/agents.db`
- Clean: `python scripts/cleanup.py`

## File Locations

- **Database:** `data/agents.db`
- **Logs:** `logs/extractor.log`
- **Exports:** Root directory (timestamped .xlsx files)
- **Config:** `.env` and `config/config.py`

## Need More Help?

- 📖 Read `NEXT_STEPS.md` for detailed instructions
- 🔍 Read `IMPROVEMENTS_SUMMARY.md` for technical details
- 📋 Check `README.md` for full documentation
- 📊 Check `PROJECT_SUMMARY.md` for project overview

---

**Quick Stats Check:**
```bash
python check_db.py
```

**Start Scraping Now:**
```bash
python parallel_scraper.py --workers 2 --start-page 1 --pages 10
```

Good luck! 🎉
