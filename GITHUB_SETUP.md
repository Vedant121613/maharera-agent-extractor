# GitHub Setup Guide - MahaRERA Scraper

Complete guide to push your project to GitHub and deploy on AWS.

---

## 📦 What Will Be Pushed to GitHub

**Included (code only, ~50KB):**
- ✅ All Python source code
- ✅ Configuration files
- ✅ Documentation (README, guides)
- ✅ Requirements and setup scripts

**Excluded (your local data is safe):**
- ❌ Database files (`data/agents.db`) - stays on your PC
- ❌ Log files (`logs/`) - stays on your PC
- ❌ API keys (`.env`) - stays on your PC
- ❌ Scraped data - stays on your PC

**GitHub repo size:** ~50-100KB (very small!)

---

## 🚀 Step 1: Prepare Project

### 1.1 Check Current Data
```bash
python check_db.py
```
Note: **370 pages = ~3,700 agents** are safe in `data/agents.db` on your PC.

### 1.2 Clean up (already done!)
- ✅ CAPTCHA attempts: 7
- ✅ Requirements: Only free packages
- ✅ .gitignore: Created (protects your data)

---

## 🔑 Step 2: Create GitHub Repository

### 2.1 Go to GitHub
- Login to: https://github.com
- Click: **"New"** or **"+"** → **"New repository"**

### 2.2 Configure Repository
- **Repository name:** `maharera-agent-extractor`
- **Description:** `MahaRERA agent data scraper with free Tesseract OCR`
- **Visibility:** 
  - ✅ **Private** (recommended - keeps your project private)
  - ⬜ Public (if you want to share)
- **Initialize:** 
  - ⬜ Don't add README (we have one)
  - ⬜ Don't add .gitignore (we have one)
- Click: **"Create repository"**

---

## 📤 Step 3: Push Code to GitHub

### 3.1 Initialize Git (if not done)
```bash
cd D:\pureframe_lab\maharera-agent-extractor
git init
```

### 3.2 Configure Git (first time only)
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 3.3 Stage Files
```bash
# Add all files (excluding data/logs via .gitignore)
git add .

# Check what will be committed
git status
```

**Verify:** Should show code files only, NO `data/`, `logs/`, or `.env`

### 3.4 Commit
```bash
git commit -m "Initial commit: MahaRERA scraper with free Tesseract OCR (7 attempts)"
```

### 3.5 Connect to GitHub
```bash
# Replace YOUR-USERNAME with your GitHub username
git remote add origin https://github.com/YOUR-USERNAME/maharera-agent-extractor.git
```

### 3.6 Push to GitHub
```bash
git branch -M main
git push -u origin main
```

**Enter GitHub credentials when prompted.**

---

## ✅ Step 4: Verify Upload

1. Go to: `https://github.com/YOUR-USERNAME/maharera-agent-extractor`
2. Check files are uploaded
3. **Verify data is NOT there:**
   - ❌ No `data/` folder
   - ❌ No `logs/` folder
   - ❌ No `.env` file

---

## 🌐 Step 5: Deploy to AWS from GitHub

### 5.1 Launch EC2 (as before)
- Ubuntu 22.04, t3.xlarge, 50GB

### 5.2 Connect and Setup
```bash
ssh -i "maharera-key.pem" ubuntu@YOUR-EC2-IP

# Install dependencies
sudo apt update
sudo apt install -y python3-pip tesseract-ocr git
```

### 5.3 Clone from GitHub
```bash
cd ~
git clone https://github.com/YOUR-USERNAME/maharera-agent-extractor.git
cd maharera-agent-extractor
```

### 5.4 Setup Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt
playwright install chromium

# Create .env file
cp .env.example .env
nano .env
# Edit: Set HEADLESS=true, TESSERACT_CMD=/usr/bin/tesseract
```

### 5.5 Create Data Directories
```bash
mkdir -p data logs output
```

---

## 🏃 Step 6: Run Multiple Workers (10 workers × 50 pages each)

### Worker Configuration:
- **10 EC2 instances** OR **10 parallel processes on 1 instance**
- Each handles **50 pages** = 500 pages total

### Option A: Single EC2 with 10 Workers (Recommended)
```bash
# t3.2xlarge (8 vCPU, 32GB RAM) - Can handle 10 workers
# Cost: ~$0.33/hour = ~$24 for 3 days

cd ~/maharera-agent-extractor
source venv/bin/activate

# Run 10 workers, pages 371-870 (next 500 pages after your 370)
nohup python3 parallel_scraper.py --workers 10 --start-page 371 --pages 500 --headless > scraper.log 2>&1 &
```

### Option B: 10 Separate Commands (1 instance, 10 terminals)
```bash
# Terminal 1
python3 main.py --scrape --start-page 371 --pages 50 --headless &

# Terminal 2
python3 main.py --scrape --start-page 421 --pages 50 --headless &

# Terminal 3
python3 main.py --scrape --start-page 471 --pages 50 --headless &

# ... and so on for workers 4-10
```

---

## 📊 Step 7: Monitor All Workers

### Check all running:
```bash
ps aux | grep python | wc -l
# Should show 10 (or 11 if you count grep)
```

### Monitor database growth:
```bash
watch -n 30 'python3 check_db.py'
# Updates every 30 seconds
```

### Check individual worker logs:
```bash
tail -f logs/extractor.log
```

---

## 💾 Step 8: Merge Data

### After AWS scraping completes:

#### Download AWS database:
```powershell
# From your Windows PC:
scp -i "maharera-key.pem" ubuntu@YOUR-EC2-IP:~/maharera-agent-extractor/data/agents.db ./agents_aws.db
```

#### Merge with your local database:
```bash
# On your Windows PC:
python merge_databases.py
```

I'll create the merge script for you.

---

## 🔄 Step 9: Update GitHub (After Changes)

```bash
cd D:\pureframe_lab\maharera-agent-extractor

# Check changes
git status

# Add changes
git add .

# Commit
git commit -m "Updated: CAPTCHA attempts to 7, cleaned dependencies"

# Push
git push
```

---

## 📈 Storage Estimates

### GitHub Repository:
- **Code only:** ~50-100KB
- **Free tier limit:** 1GB (you'll use <1%)
- **Private repos:** Unlimited (free)

### AWS EC2:
- **50GB disk:** More than enough
- **Database:** ~50-100MB for 58,000 agents
- **Logs:** ~500MB-1GB

### Your PC:
- **Current (370 pages):** ~4-5MB
- **After 500 more pages:** ~10MB total
- **Full 5,849 pages:** ~100MB

---

## 🎯 Recommended Workflow

**Phase 1: Pages 1-370 (DONE ✓)**
- Your PC, 370 pages completed
- Data: `D:\pureframe_lab\maharera-agent-extractor\data\agents.db`

**Phase 2: Pages 371-870 (NEXT)**
- AWS EC2, 10 workers, 500 pages
- Data: Download from AWS

**Phase 3: Pages 871-5849 (LATER)**
- AWS EC2, continue from page 871
- Data: Merge all databases

---

## ⚠️ Important Notes

1. **Your 370 pages of data is SAFE:**
   - Stored locally: `data/agents.db`
   - NOT pushed to GitHub
   - Backup before pushing!

2. **API Keys are SAFE:**
   - `.env` file NOT pushed to GitHub
   - Each deployment uses `.env.example` as template

3. **GitHub Free Tier:**
   - Unlimited private repos
   - 1GB storage (you'll use <1%)
   - Unlimited collaborators

4. **AWS Costs:**
   - t3.2xlarge: ~$0.33/hour
   - 500 pages @ 10 workers: ~2-3 days = $16-24
   - Your $100 credits: Plenty left!

---

## 🆘 Troubleshooting

### Git says "file too large":
- Check `.gitignore` is working
- Run: `git rm --cached data/*` to remove data

### Can't push to GitHub:
- Check internet connection
- Verify GitHub credentials
- Try: `git remote -v` to verify URL

### Lost data during push:
- Don't worry! Data is local only
- Check: `D:\pureframe_lab\maharera-agent-extractor\data\agents.db`
- It's never uploaded to GitHub

---

## ✅ Quick Checklist

Before pushing to GitHub:
- [ ] Backup your `data/agents.db` file
- [ ] Check `.gitignore` exists
- [ ] Verify CAPTCHA attempts = 7
- [ ] Requirements cleaned (no OpenAI/Claude)
- [ ] `.env.example` created (no secrets)

After pushing to GitHub:
- [ ] Verify data/ not in repo
- [ ] Verify logs/ not in repo
- [ ] Verify .env not in repo
- [ ] Clone to AWS works

Running on AWS:
- [ ] 10 workers started
- [ ] Monitoring working
- [ ] Database growing
- [ ] No errors in logs

---

**🎉 Ready to push to GitHub!**

**Next commands:**
```bash
cd D:\pureframe_lab\maharera-agent-extractor
git init
git add .
git commit -m "Initial commit: Free Tesseract scraper with 7 attempts"
git remote add origin https://github.com/YOUR-USERNAME/maharera-agent-extractor.git
git push -u origin main
```
