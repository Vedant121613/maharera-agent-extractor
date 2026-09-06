# AWS Deployment - Pull Latest Code

## 🚀 Quick Deploy to AWS

### Step 1: Connect to Your AWS EC2 Instance

```bash
# From your local machine (Git Bash or PowerShell with SSH)
ssh -i "your-key.pem" ubuntu@your-ec2-public-ip

# Example:
# ssh -i "maharera-key.pem" ubuntu@54.123.456.789
```

### Step 2: Navigate to Project Directory

```bash
cd maharera-agent-extractor
```

### Step 3: Pull Latest Code from GitHub

```bash
# Ensure you're on main branch
git branch

# Pull latest changes
git pull origin main

# Verify changes
git log --oneline -n 5
```

You should see:
```
bb43fce Add comprehensive documentation for improved scraper
7e0d479 Improve parallel scraper stability and add monitoring utilities
...
```

### Step 4: Activate Virtual Environment

```bash
source venv/bin/activate
```

### Step 5: Update Dependencies (if needed)

```bash
# Check if requirements changed
pip install -r requirements.txt --upgrade
```

### Step 6: Verify Setup

```bash
# Check database status
python check_db.py

# Verify Playwright
playwright --version
```

### Step 7: Test the Updated Scraper

```bash
# Small test run
python parallel_scraper.py --workers 1 --start-page 1 --pages 5

# Check results
python check_recent.py
```

### Step 8: Run Production Scraping

```bash
# Option 1: Run in foreground
python parallel_scraper.py --workers 3 --start-page 1 --pages 100

# Option 2: Run in background with nohup
nohup python parallel_scraper.py --workers 3 --start-page 1 --pages 500 > scraper.log 2>&1 &

# Option 3: Use screen for detached session
screen -S scraper
python parallel_scraper.py --workers 3 --start-page 1 --pages 500
# Press Ctrl+A then D to detach
# screen -r scraper  # to reattach
```

---

## 🔄 Complete Step-by-Step Commands

Copy and paste these commands one by one:

```bash
# 1. Connect to EC2
ssh -i "your-key.pem" ubuntu@your-ec2-ip

# 2. Navigate and pull
cd maharera-agent-extractor
git pull origin main

# 3. Activate environment
source venv/bin/activate

# 4. Update dependencies
pip install -r requirements.txt --upgrade

# 5. Check status
python check_db.py

# 6. Test small batch
python parallel_scraper.py --workers 1 --start-page 1 --pages 3

# 7. If successful, run production
nohup python parallel_scraper.py --workers 3 --start-page 1 --pages 500 > scraper.log 2>&1 &

# 8. Monitor progress
tail -f scraper.log

# Or in another terminal
python monitor_live.py
```

---

## 📊 Monitoring on AWS

### Real-time Log Monitoring
```bash
# Terminal 1: Watch logs
tail -f logs/extractor.log

# Terminal 2: Monitor live stats
python monitor_live.py

# Check process
ps aux | grep python
```

### Check Progress
```bash
# Database stats
python check_db.py

# Recent collections
python check_recent.py -n 20

# Failed agents
python check_failed.py

# CAPTCHA performance
python captcha_stats.py
```

---

## 🛠️ Troubleshooting on AWS

### If Git Pull Fails

```bash
# Check current status
git status

# If there are local changes, stash them
git stash

# Pull again
git pull origin main

# Apply stashed changes if needed
git stash pop
```

### If Playwright Needs Reinstall

```bash
# Reinstall Playwright browsers
playwright install chromium

# If chromium fails, install dependencies
sudo playwright install-deps chromium
```

### If Process Gets Killed

```bash
# Check memory
free -h

# Check disk space
df -h

# If low memory, reduce workers
python parallel_scraper.py --workers 1 --start-page 1 --pages 100
```

### Check Running Processes

```bash
# List Python processes
ps aux | grep python

# Kill a process if needed
kill -9 <PID>

# Or use pkill
pkill -f "parallel_scraper"
```

---

## 🔐 Security Checks

### Verify .env File is Not Tracked
```bash
# This should NOT show .env
git ls-files | grep ".env"

# Check .gitignore includes .env
cat .gitignore | grep ".env"
```

### Ensure Data Files are Excluded
```bash
# These should be empty or not exist
git ls-files | grep "data/"
git ls-files | grep ".db"
git ls-files | grep "logs/"
```

---

## 📦 Download Results from AWS

### Using SCP (from your local machine)

```bash
# Download database
scp -i "your-key.pem" ubuntu@your-ec2-ip:~/maharera-agent-extractor/data/agents.db ./agents_aws.db

# Download Excel exports
scp -i "your-key.pem" ubuntu@your-ec2-ip:~/maharera-agent-extractor/*.xlsx ./

# Download logs
scp -i "your-key.pem" ubuntu@your-ec2-ip:~/maharera-agent-extractor/logs/extractor.log ./aws_logs.log
```

### Using AWS CLI (if configured)

```bash
# Upload to S3
aws s3 cp data/agents.db s3://your-bucket/maharera/agents.db
aws s3 cp *.xlsx s3://your-bucket/maharera/
```

---

## 🎯 Recommended AWS Workflow

### Initial Deployment (First Time)
```bash
# 1. Connect
ssh -i "your-key.pem" ubuntu@your-ec2-ip

# 2. Clone repo (if not already done)
git clone https://github.com/yourusername/maharera-agent-extractor.git
cd maharera-agent-extractor

# 3. Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
sudo playwright install-deps chromium

# 4. Configure
cp .env.example .env
nano .env  # Edit configuration

# 5. Test
python check_db.py
python main.py --start-page 1 --pages 1
```

### Update Deployment (What You're Doing Now)
```bash
# 1. Connect
ssh -i "your-key.pem" ubuntu@your-ec2-ip

# 2. Update
cd maharera-agent-extractor
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 3. Test
python check_db.py
python parallel_scraper.py --workers 1 --start-page 1 --pages 3

# 4. Deploy
nohup python parallel_scraper.py --workers 3 --start-page 1 --pages 500 > scraper.log 2>&1 &

# 5. Monitor
tail -f scraper.log
```

---

## 🚨 Important Notes

### Worker Count on AWS
- **t2.micro (1 GB RAM):** Use `--workers 1`
- **t2.small (2 GB RAM):** Use `--workers 1-2`
- **t2.medium (4 GB RAM):** Use `--workers 2-3`
- **t2.large (8 GB RAM):** Use `--workers 3-5`

### Network Considerations
- AWS has good bandwidth, so scraping will be faster
- Watch for rate limiting from MahaRERA website
- Use appropriate delays in config.py

### Storage
- Check disk space regularly: `df -h`
- Database can grow large with many agents
- Consider using EBS volume if needed

### Cost Optimization
- Stop instance when not scraping: `sudo shutdown -h now`
- Use spot instances for cost savings
- Monitor AWS billing dashboard

---

## 📋 Quick Reference Commands

```bash
# Connect
ssh -i "key.pem" ubuntu@ec2-ip

# Update code
cd maharera-agent-extractor && git pull origin main

# Activate environment
source venv/bin/activate

# Run scraper (background)
nohup python parallel_scraper.py --workers 2 --start-page 1 --pages 500 > scraper.log 2>&1 &

# Monitor
tail -f scraper.log
python monitor_live.py

# Check stats
python check_db.py
python check_recent.py

# Download results (from local machine)
scp -i "key.pem" ubuntu@ec2-ip:~/maharera-agent-extractor/data/agents.db ./
```

---

## ✅ Deployment Checklist

- [ ] Connected to AWS EC2
- [ ] Navigated to project directory
- [ ] Pulled latest code from GitHub
- [ ] Activated virtual environment
- [ ] Updated dependencies
- [ ] Verified setup with check_db.py
- [ ] Tested with small batch
- [ ] Started production scraping
- [ ] Monitoring progress
- [ ] Scheduled result download

---

**Next Step:** Connect to your AWS instance and run the commands above! 🚀

**Need the detailed AWS setup?** Check `AWS_DEPLOYMENT_GUIDE.md`
