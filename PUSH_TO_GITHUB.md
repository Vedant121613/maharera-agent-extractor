# 🚀 Push to GitHub - Complete Guide

Your project is **100% ready** for GitHub! Here's everything cleaned and prepared.

---

## ✅ What We've Done

### 1. **Cleaned Files**
- ❌ Deleted `captcha/openai_solver.py` (unused)
- ❌ Deleted `captcha/claude_solver.py` (unused)
- ❌ Deleted `captcha/third_party.py` (unused 2Captcha)
- ❌ Deleted `test_openai.py` (test file)
- ✅ Using **ONLY FREE Tesseract OCR**

### 2. **Updated Configuration**
- ✅ CAPTCHA attempts: **7** (increased from 5)
- ✅ `config/config.py`: Removed OpenAI/Claude API keys
- ✅ `.env`: Cleaned, ready for AWS
- ✅ `requirements.txt`: Only FREE packages

### 3. **Created GitHub Files**
- ✅ `.gitignore` - Protects your data/logs/.env
- ✅ `.env.example` - Template for new deployments
- ✅ `README.md` - Professional documentation
- ✅ `GITHUB_SETUP.md` - Step-by-step guide
- ✅ `AWS_DEPLOYMENT_GUIDE.md` - AWS instructions
- ✅ `aws_deploy.sh` - One-command AWS setup
- ✅ `merge_databases.py` - Merge local + AWS data

### 4. **Your Data is Safe**
- ✅ **3,675 agents** in `data/agents.db` (NOT pushed to GitHub)
- ✅ All logs stay local
- ✅ No API keys in repo

---

## 📦 Repository Size

**Code only:** ~50-100 KB
**Your data (local only):** ~5-10 MB (3,675 agents)

**GitHub will contain:**
- Python source code
- Documentation
- Configuration templates
- NO data, NO logs, NO secrets

---

## 🎯 Push to GitHub (3 Easy Steps)

### Step 1: Create GitHub Repository

1. Go to: https://github.com/new
2. **Repository name:** `maharera-agent-extractor`
3. **Description:** `MahaRERA agent scraper with FREE Tesseract OCR (7 attempts)`
4. **Visibility:** 
   - ✅ **Private** (recommended)
   - ⬜ Public
5. **Initialize:** ⬜ DON'T check any boxes
6. Click: **"Create repository"**

### Step 2: Configure Git (First Time Only)

```powershell
# Set your name and email
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Step 3: Push Code

```powershell
# Navigate to project
cd D:\pureframe_lab\maharera-agent-extractor

# Initialize Git
git init

# Add all files (data/logs excluded by .gitignore)
git add .

# Verify what will be pushed
git status

# You should see:
# ✅ All .py files
# ✅ README.md, requirements.txt, etc.
# ❌ NO data/ folder
# ❌ NO logs/ folder
# ❌ NO .env file

# Commit
git commit -m "Initial commit: Free Tesseract OCR scraper (7 attempts, AWS optimized)"

# Connect to GitHub (replace YOUR-USERNAME)
git remote add origin https://github.com/YOUR-USERNAME/maharera-agent-extractor.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Enter your GitHub username and password (or token) when prompted.**

---

## 🔍 Verify Push

1. Go to: `https://github.com/YOUR-USERNAME/maharera-agent-extractor`
2. **Check these files exist:**
   - ✅ `README.md`
   - ✅ `requirements.txt`
   - ✅ `.gitignore`
   - ✅ `main.py`, `parallel_scraper.py`
   - ✅ All folders: `api/`, `browser/`, `captcha/`, etc.

3. **Verify these DON'T exist:**
   - ❌ `data/` folder
   - ❌ `logs/` folder
   - ❌ `.env` file
   - ❌ `test_openai.py`
   - ❌ `captcha/openai_solver.py`
   - ❌ `captcha/claude_solver.py`

---

## 🌐 Deploy to AWS EC2

### Recommended Instance: **t3.xlarge**
- **vCPU:** 4 cores
- **RAM:** 16 GB
- **Workers:** 10 parallel browsers
- **Cost:** ~$0.17/hour = ~$4/day
- **Your $100 credits:** Can run for 25 days!

### Quick AWS Setup

```bash
# SSH into EC2 (Ubuntu 22.04)
ssh -i "maharera-key.pem" ubuntu@YOUR-EC2-IP

# Clone from GitHub
git clone https://github.com/YOUR-USERNAME/maharera-agent-extractor.git
cd maharera-agent-extractor

# Run deployment script
bash aws_deploy.sh

# Script will:
# - Install Tesseract OCR
# - Create Python environment
# - Install all dependencies
# - Setup directories
# - Configure .env for AWS
```

---

## 🏃 Run 10 Workers on AWS

### Option 1: Background Process (Recommended)

```bash
# Activate environment
source venv/bin/activate

# Run 10 workers, pages 1-500 (or 371-870 to continue after your local 370)
nohup python3 parallel_scraper.py \
  --workers 10 \
  --start-page 371 \
  --pages 500 \
  --headless \
  > scraper.log 2>&1 &

# Get process ID
echo $!

# Monitor progress
tail -f scraper.log
python3 check_db.py
```

### Option 2: Using tmux (Better)

```bash
# Start tmux session
tmux new -s scraper

# Run scraper
source venv/bin/activate
python3 parallel_scraper.py --workers 10 --start-page 371 --pages 500 --headless

# Detach: Press Ctrl+B, then D
# Reattach later: tmux attach -t scraper
```

---

## 📊 Monitor Progress

### Check database stats:
```bash
python3 check_db.py
```

### Watch live (updates every 30 seconds):
```bash
watch -n 30 'python3 check_db.py'
```

### View logs:
```bash
tail -f logs/extractor.log | grep -E "CAPTCHA|Collected|Failed"
```

### Check running workers:
```bash
ps aux | grep python | wc -l
# Should show 10 (or 11 counting grep)
```

---

## 💾 Merge AWS Data with Local Data

### After AWS scraping completes:

#### 1. Download AWS database:
```powershell
# From your Windows PC
scp -i "maharera-key.pem" ubuntu@YOUR-EC2-IP:~/maharera-agent-extractor/data/agents.db ./agents_aws.db
```

#### 2. Merge databases:
```powershell
# On your Windows PC
cd D:\pureframe_lab\maharera-agent-extractor
python merge_databases.py

# Output example:
# Source: agents_aws.db (5,000 agents)
# Target: data/agents.db (3,675 agents)
# Added: 4,850 new agents
# Skipped: 150 duplicates
# Total: 8,525 agents
```

---

## 📈 Expected Results

### Your Current Data (Local PC):
- **Pages scraped:** ~370
- **Agents collected:** 3,675
- **Success rate:** ~82%

### After AWS (10 workers × 500 pages):
- **Additional pages:** 500
- **Expected new agents:** ~4,500-5,000
- **Total:** ~8,000-8,500 agents
- **Time:** 2-3 days

### Full Dataset (5,849 pages):
- **Total agents:** ~58,000
- **Time on AWS (10 workers):** 20-25 days
- **Cost:** ~$80-100 (your credits!)

---

## 💡 Cost Breakdown

### AWS t3.xlarge:
- **Hourly:** $0.17/hour
- **Daily:** $4.08/day
- **500 pages (2-3 days):** $8-12
- **Full dataset (25 days):** $100

**Your $100 AWS credits = Perfect for complete scraping!**

---

## ⚠️ Important Notes

### Before Pushing to GitHub:

1. **Backup your database:**
   ```powershell
   copy data\agents.db data\agents_backup_$(date +%Y%m%d).db
   ```

2. **Verify .gitignore working:**
   ```powershell
   git status
   # Should NOT show data/ or logs/
   ```

3. **Check no secrets:**
   ```powershell
   # Make sure .env is NOT listed
   git status | findstr .env
   # Should only show .env.example
   ```

### After Pushing:

1. **Clone on AWS works:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/maharera-agent-extractor.git
   # Should work without authentication (public) or with credentials (private)
   ```

2. **Your local data is untouched:**
   ```powershell
   dir data\agents.db
   # Should still exist
   ```

---

## 🔄 Update GitHub Later

If you make changes:

```powershell
cd D:\pureframe_lab\maharera-agent-extractor

# Check changes
git status

# Add changes
git add .

# Commit
git commit -m "Updated: Fixed X, improved Y"

# Push
git push
```

---

## 🆘 Troubleshooting

### "File too large" error:
```powershell
# Check .gitignore is working
cat .gitignore | findstr data

# Remove data from Git cache
git rm -r --cached data/
git commit -m "Remove data from tracking"
git push
```

### Can't push (authentication failed):
- Use Personal Access Token instead of password
- Generate at: https://github.com/settings/tokens
- Use token as password

### Lost data:
- **Don't worry!** Data is local only
- Check: `D:\pureframe_lab\maharera-agent-extractor\data\agents.db`
- Never uploaded to GitHub (protected by .gitignore)

---

## ✅ Final Checklist

Before pushing:
- [x] CAPTCHA attempts = 7
- [x] Only FREE packages in requirements.txt
- [x] No OpenAI/Claude files
- [x] .gitignore created
- [x] .env.example created (no secrets)
- [x] Database backed up
- [ ] Git configured (name/email)
- [ ] GitHub repo created

After pushing:
- [ ] Code visible on GitHub
- [ ] data/ NOT in repo
- [ ] logs/ NOT in repo
- [ ] .env NOT in repo
- [ ] README.md shows correctly

On AWS:
- [ ] Cloned successfully
- [ ] aws_deploy.sh completed
- [ ] 10 workers running
- [ ] Database growing

---

## 🎉 Ready to Go!

**Your project is 100% ready for GitHub!**

**Next command:**
```powershell
cd D:\pureframe_lab\maharera-agent-extractor
git init
git add .
git commit -m "Initial commit: Free Tesseract OCR scraper (7 attempts, 16GB RAM optimized)"
git remote add origin https://github.com/YOUR-USERNAME/maharera-agent-extractor.git
git push -u origin main
```

**Questions?**
- Check `GITHUB_SETUP.md` for detailed guide
- Check `AWS_DEPLOYMENT_GUIDE.md` for AWS steps
- All your data is safe in `data/agents.db` (3,675 agents)

**Good luck with your scraping! 🚀**
