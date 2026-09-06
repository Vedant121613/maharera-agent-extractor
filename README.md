# MahaRERA Agent Data Extractor

Automated scraper for extracting agent contact data from [MahaRERA](https://maharerait.maharashtra.gov.in) using **FREE Tesseract OCR**.

## 🎯 Features

- ✅ **100% FREE** - Uses Tesseract OCR (no API costs)
- ✅ **Network interception** - Captures real unmasked data from API
- ✅ **7 CAPTCHA attempts** - Better success rate (~30-40%)
- ✅ **Parallel processing** - Run 10+ browsers simultaneously
- ✅ **AWS EC2 optimized** - Designed for t3.xlarge (16GB RAM)
- ✅ **SQLite database** - Concurrent write support with WAL mode
- ✅ **Excel export** - Easy data export

## 📊 Data Extracted

- **Contact:** Mobile, alternate mobile, office phone, email, website
- **Address:** Building, street, locality, landmark, city, taluka, district, state, pincode
- **General:** Name, certificate no, registration dates, status

## 🚀 Quick Start

### Local (Windows/Mac/Linux)

```bash
# Clone repository
git clone https://github.com/YOUR-USERNAME/maharera-agent-extractor.git
cd maharera-agent-extractor

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Install Tesseract OCR
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# Linux: sudo apt install tesseract-ocr
# Mac: brew install tesseract

# Configure
cp .env.example .env
nano .env  # Set TESSERACT_CMD path

# Run scraper
python main.py --scrape --pages 10 --no-headless
```

### AWS EC2 (Recommended for large scale)

```bash
# Launch t3.xlarge Ubuntu 22.04 (16GB RAM)
# SSH into instance

# Clone and setup
git clone https://github.com/YOUR-USERNAME/maharera-agent-extractor.git
cd maharera-agent-extractor
bash aws_deploy.sh

# Run 10 parallel workers
nohup python3 parallel_scraper.py --workers 10 --start-page 1 --pages 500 --headless &
```

## 💻 System Requirements

| Setup | CPU | RAM | Workers | Speed |
|-------|-----|-----|---------|-------|
| Local (minimum) | 2 cores | 4GB | 2-3 | Slow |
| Local (recommended) | 4 cores | 8GB | 5 | Medium |
| **AWS t3.xlarge** | 4 vCPU | 16GB | **10** | **Fast** |
| AWS t3.2xlarge | 8 vCPU | 32GB | 15+ | Very Fast |

## 📖 Usage

### Basic Scraping

```bash
# Scrape 10 pages (100 agents)
python main.py --scrape --pages 10

# Start from specific page
python main.py --scrape --start-page 100 --pages 50

# Run in background (headless)
python main.py --scrape --pages 100 --headless
```

### Parallel Scraping (10 workers)

```bash
# 10 workers, pages 1-500
python parallel_scraper.py --workers 10 --start-page 1 --pages 500 --headless

# Monitor progress
python check_db.py
python monitor_live.py
```

### Export Data

```bash
# Export to Excel
python main.py --export excel --output agents_data

# Check CAPTCHA stats
python captcha_stats.py
```

## 📁 Project Structure

```
maharera-agent-extractor/
├── api/                    # API endpoint handlers
├── browser/                # Playwright browser management
├── captcha/                # Tesseract OCR CAPTCHA solver
├── config/                 # Configuration
├── database/               # SQLite database layer
├── exporter/               # Excel/CSV exporters
├── scraper/                # Search & detail page scrapers
├── data/                   # SQLite database (gitignored)
├── logs/                   # Log files (gitignored)
├── main.py                 # Single worker entry point
├── parallel_scraper.py     # Multi-worker entry point
├── requirements.txt        # Python dependencies
└── .env.example            # Environment template
```

## ⚙️ Configuration

Edit `.env`:

```env
# Browser
HEADLESS=true

# CAPTCHA - FREE Tesseract OCR with 7 attempts
CAPTCHA_SOLVER_TYPE=local
TESSERACT_CMD=/usr/bin/tesseract

# Rate limiting (faster)
REQUEST_DELAY_MIN=1.0
REQUEST_DELAY_MAX=2.0
```

## 📈 Performance

### CAPTCHA Success Rate
- **Tesseract OCR:** 30-40% (FREE)
- **7 attempts per agent:** Better than 2-5 attempts

### Speed Estimates (t3.xlarge, 10 workers)
- **500 pages:** 2-3 days
- **5,849 pages (all):** 20-25 days

### Cost (AWS t3.xlarge)
- **$0.17/hour** = ~$4/day = **$10-12 for 500 pages**
- Your $100 AWS credits: Can scrape 2,000-2,500 pages

## 🔄 Workflow

### Phase 1: Local Development (✓ Done)
- 370 pages completed on your PC
- Data saved in `data/agents.db`

### Phase 2: AWS Deployment (Next)
```bash
# Upload to GitHub
git init
git add .
git commit -m "Initial commit: Free Tesseract scraper"
git remote add origin https://github.com/YOUR-USERNAME/maharera-agent-extractor.git
git push -u origin main

# Deploy on AWS
# (Follow AWS_DEPLOYMENT_GUIDE.md)

# Scrape pages 371-870 (500 pages)
python3 parallel_scraper.py --workers 10 --start-page 371 --pages 500 --headless

# Download results
scp -i key.pem ubuntu@IP:~/maharera-scraper/data/agents.db ./agents_aws.db

# Merge databases
python merge_databases.py
```

## 🛠️ Troubleshooting

### CAPTCHA not solving
```bash
# Check Tesseract installation
tesseract --version

# View CAPTCHA debug image
# File: captcha_debug.png

# Check logs
tail -f logs/extractor.log | grep CAPTCHA
```

### Database locked errors
- Already fixed with 30s timeout and WAL mode
- Just wait, will retry automatically

### Browser crashes
- Reduce workers: `--workers 5` instead of 10
- Increase RAM on AWS (t3.2xlarge)

## 📊 Data Quality

Based on 370 pages collected:
- **Success rate:** ~70%
- **With contact data:** ~60%
- **Complete records:** ~50%

## 🔒 Security

- ✅ `.env` not committed (API keys safe)
- ✅ `data/` not committed (your data safe)
- ✅ `logs/` not committed (privacy)
- ✅ `.gitignore` configured properly

## 📝 License

MIT License - See LICENSE file

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 💡 Tips

1. **Start small:** Test with 10 pages before running 500
2. **Monitor regularly:** Check `python check_db.py` every few hours
3. **Backup data:** Copy database before merging
4. **Stop AWS when done:** Save your credits!

## 📞 Support

- **Issues:** GitHub Issues
- **Logs:** Check `logs/extractor.log`
- **Database:** Use `python check_db.py` to inspect

---

**⚠️ Disclaimer:** This scraper is for educational purposes. Ensure you comply with MahaRERA's terms of service and robots.txt. Use responsibly and respect rate limits.

---

**Made with ❤️ for data extraction automation**
