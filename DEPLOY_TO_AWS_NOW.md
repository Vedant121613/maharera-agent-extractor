# 🚀 Deploy to AWS RIGHT NOW - Simple Steps

## Step 1: Open Your AWS Connection Tool

Use one of these:
- **Git Bash** (if installed)
- **PowerShell with SSH**
- **PuTTY** (if you have it configured)
- **AWS EC2 Instance Connect** (from AWS Console)

---

## Step 2: Connect to Your EC2 Instance

### If you have the .pem key file:
```bash
ssh -i "path/to/your-key.pem" ubuntu@your-ec2-public-ip
```

### Example:
```bash
ssh -i "C:/Users/Vedant/maharera-key.pem" ubuntu@54.123.456.789
```

### Or use AWS Console:
1. Go to EC2 Dashboard
2. Select your instance
3. Click "Connect"
4. Choose "EC2 Instance Connect"
5. Click "Connect"

---

## Step 3: Copy-Paste These Commands

Once connected to AWS, copy and paste each line:

```bash
# Navigate to project
cd maharera-agent-extractor

# Pull latest code
git pull origin main

# Activate environment
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt --upgrade

# Check status
python check_db.py
```

---

## Step 4: Test the Update

```bash
# Small test
python parallel_scraper.py --workers 1 --start-page 1 --pages 3
```

If this works, proceed to production scraping.

---

## Step 5: Start Production Scraping

Choose one option:

### Option A: Run in Background (Recommended)
```bash
nohup python parallel_scraper.py --workers 3 --start-page 1 --pages 500 > scraper.log 2>&1 &
```

Then monitor with:
```bash
tail -f scraper.log
```

Press `Ctrl+C` to stop watching (scraper keeps running)

### Option B: Use Screen (Detachable)
```bash
screen -S scraper
python parallel_scraper.py --workers 3 --start-page 1 --pages 500

# Press Ctrl+A then D to detach
# To reattach later: screen -r scraper
```

### Option C: Run in Foreground
```bash
python parallel_scraper.py --workers 3 --start-page 1 --pages 500
```

---

## Step 6: Monitor Progress

### Check in Real-Time:
```bash
# In another SSH session
python monitor_live.py
```

### Check Database Stats:
```bash
python check_db.py
```

### View Recent Collections:
```bash
python check_recent.py
```

---

## Quick Copy-Paste Full Script

```bash
cd maharera-agent-extractor
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
python check_db.py
python parallel_scraper.py --workers 1 --start-page 1 --pages 3
nohup python parallel_scraper.py --workers 3 --start-page 1 --pages 500 > scraper.log 2>&1 &
tail -f scraper.log
```

---

## If You Need Help

### Git Pull Fails?
```bash
git stash
git pull origin main
```

### Can't Find Virtual Environment?
```bash
# Check if it exists
ls -la venv/

# If not, create it
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Process Gets Killed?
```bash
# Check memory
free -h

# Reduce workers
python parallel_scraper.py --workers 1 --start-page 1 --pages 100
```

### Check if Process is Running:
```bash
ps aux | grep python
```

### Stop Running Process:
```bash
pkill -f "parallel_scraper"
```

---

## Download Results Later

From your **local Windows machine**:

```powershell
# Download database
scp -i "path/to/key.pem" ubuntu@ec2-ip:~/maharera-agent-extractor/data/agents.db ./agents_aws.db

# Download Excel files
scp -i "path/to/key.pem" ubuntu@ec2-ip:~/maharera-agent-extractor/*.xlsx ./
```

---

## What You Should See

### After git pull:
```
From https://github.com/yourusername/maharera-agent-extractor
 * branch            main       -> FETCH_HEAD
Updating 8b44125..f6f3f25
Fast-forward
 .gitignore                   |   3 -
 parallel_scraper.py          |  60 ++++++++---
 captcha_stats.py             |  50 +++++++++
 check_db.py                  |  40 +++++++
 ...
```

### After test run:
```
╔══════════════════════════════════════════════════════════════╗
║  🚀 PARALLEL SCRAPER - 1 WORKERS                        ║
╚══════════════════════════════════════════════════════════════╝

  Pages: 1 to 3
  Workers: 1
  Mode: Headless

🚀 Worker 1 starting - pages 1 to 3
📄 Worker 1 - Page 1
Found 10 agents on page 1
✅ Agent A12345 - 9876543210 | agent@example.com
...
```

---

## 🎯 That's It!

Your code is now updated on AWS and ready to run at full scale.

**Next:** Just run the production command and monitor progress!

```bash
nohup python parallel_scraper.py --workers 3 --start-page 1 --pages 500 > scraper.log 2>&1 &
tail -f scraper.log
```

Good luck! 🚀
