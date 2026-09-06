# MahaRERA Scraper - AWS EC2 Deployment Guide

Complete guide to deploy and run your scraper on AWS EC2 with $100 free credits.

---

## 📋 Prerequisites

- AWS account with $100 free credits
- Your scraper code ready
- Windows PowerShell or Terminal

---

## 🚀 Step 1: Launch EC2 Instance

### 1.1 Go to AWS Console
- Login to: https://console.aws.amazon.com/
- Search for "EC2" and click it

### 1.2 Launch Instance
Click **"Launch Instance"** button

**Configure:**
- **Name:** `maharera-scraper`
- **OS:** Ubuntu Server 22.04 LTS (Free tier eligible)
- **Instance Type:** `t3.xlarge` (4 vCPU, 16GB RAM)
  - Cost: ~$0.17/hour = ~$12-15 for 3 days
  - Can run 10 parallel browsers
- **Key Pair:** 
  - Create new → Name: `maharera-key`
  - Download `maharera-key.pem` (SAVE THIS!)
- **Network:**
  - ✅ Allow SSH (port 22)
  - Source: My IP
- **Storage:** 50 GB
- **Click "Launch Instance"**

### 1.3 Wait for Instance to Start
- Status should show "Running" (green)
- Note the **Public IPv4 address** (e.g., 3.145.67.89)

---

## 🔌 Step 2: Connect to EC2

### Windows PowerShell:

```powershell
# Fix key permissions (important!)
icacls maharera-key.pem /inheritance:r
icacls maharera-key.pem /grant:r "%username%:R"

# Connect via SSH
ssh -i "maharera-key.pem" ubuntu@YOUR-INSTANCE-IP
# Replace YOUR-INSTANCE-IP with actual IP (e.g., 3.145.67.89)
```

Type "yes" when asked about fingerprint.

---

## 📦 Step 3: Setup EC2 Instance

### 3.1 Upload deployment script

**From your Windows PC (in NEW PowerShell window):**

```powershell
# Upload deployment script
scp -i "maharera-key.pem" "D:\pureframe_lab\maharera-agent-extractor\aws_deploy.sh" ubuntu@YOUR-INSTANCE-IP:~/
```

### 3.2 Run deployment script

**On EC2 (SSH window):**

```bash
# Make executable and run
chmod +x aws_deploy.sh
bash aws_deploy.sh
```

This installs everything automatically! ⏱️ Takes ~5-10 minutes.

---

## 📤 Step 4: Upload Your Code

**From your Windows PC (PowerShell):**

```powershell
# Upload all project files
scp -i "maharera-key.pem" -r "D:\pureframe_lab\maharera-agent-extractor\*" ubuntu@YOUR-INSTANCE-IP:~/maharera-scraper/
```

⏱️ Takes 2-5 minutes depending on internet speed.

---

## ⚙️ Step 5: Configure Environment

**On EC2:**

```bash
cd ~/maharera-scraper
source venv/bin/activate

# Edit .env file
nano .env
```

**Make sure these settings are correct:**
```env
HEADLESS=true
CAPTCHA_SOLVER_TYPE=local
REQUEST_DELAY_MIN=1.0
REQUEST_DELAY_MAX=2.0

# If using API (optional - better accuracy):
# CAPTCHA_SOLVER_TYPE=openai
# OPENAI_API_KEY=your_key_here
```

**Save:** Ctrl+O, Enter, Ctrl+X

---

## 🏃 Step 6: Run Scraper

### Test Run (1 page, 10 agents):
```bash
cd ~/maharera-scraper
source venv/bin/activate
python3 parallel_scraper.py --workers 3 --start-page 1 --pages 1 --headless
```

### Full Run (All 5,849 pages, ~58,000 agents):
```bash
nohup python3 parallel_scraper.py --workers 10 --start-page 1 --pages 5849 --headless > scraper.log 2>&1 &
```

**Explanation:**
- `nohup` - Keeps running even if you disconnect
- `--workers 10` - 10 parallel browsers (t3.xlarge can handle it)
- `--start-page 1` - Start from page 1
- `--pages 5849` - Process all pages
- `--headless` - No GUI (faster)
- `&` - Run in background

---

## 👀 Step 7: Monitor Progress

### Check if running:
```bash
ps aux | grep python
```

### View scraper output:
```bash
tail -f scraper.log
```

### View detailed logs:
```bash
tail -f logs/extractor.log
```

### Check database stats:
```bash
python3 check_db.py
```

### Monitor live:
```bash
python3 monitor_live.py
# Press Ctrl+C to stop monitoring
```

### Check CAPTCHA performance:
```bash
python3 captcha_stats.py
```

---

## 📊 Step 8: Check Progress Anytime

You can disconnect and reconnect anytime:

**Disconnect:** Type `exit` or close terminal

**Reconnect:**
```powershell
ssh -i "maharera-key.pem" ubuntu@YOUR-INSTANCE-IP
cd ~/maharera-scraper
source venv/bin/activate
python3 check_db.py
```

---

## 💾 Step 9: Download Results

### When scraping is complete:

```bash
# Export to Excel
cd ~/maharera-scraper
source venv/bin/activate
python3 main.py --export excel --output agents_final
```

### Download to your PC (PowerShell):

```powershell
# Download Excel file
scp -i "maharera-key.pem" ubuntu@YOUR-INSTANCE-IP:~/maharera-scraper/agents_final.xlsx ./

# Download database file
scp -i "maharera-key.pem" ubuntu@YOUR-INSTANCE-IP:~/maharera-scraper/data/agents.db ./

# Download logs (optional)
scp -i "maharera-key.pem" -r ubuntu@YOUR-INSTANCE-IP:~/maharera-scraper/logs ./logs_backup
```

---

## 💰 Step 10: Stop Instance (SAVE MONEY!)

**⚠️ IMPORTANT:** Stop the instance when done to avoid charges!

### Option A: Via AWS Console
1. Go to EC2 Dashboard
2. Select your instance
3. **Instance State → Stop**

### Option B: From SSH
```bash
sudo shutdown -h now
```

**Resume later:** Instance State → Start (keeps all data)

---

## 📁 Where Data is Saved

### On EC2 Instance:
```
~/maharera-scraper/
├── data/
│   ├── agents.db              ← SQLite database (main data)
│   ├── agents.db-wal          ← Write-ahead log
│   └── agents.db-shm          ← Shared memory
├── logs/
│   └── extractor.log          ← Detailed logs
├── output/
│   └── agents_final.xlsx      ← Exported Excel file
└── scraper.log                ← Console output
```

### Downloaded to Your PC:
```
D:\maharera_data\
├── agents.db                  ← Download this (complete data)
├── agents_final.xlsx          ← Download this (Excel export)
└── logs_backup\               ← Download this (for debugging)
```

---

## ⏱️ Expected Timeline

| Workers | Instance | Pages | Time | Cost (from $100) |
|---------|----------|-------|------|------------------|
| 10 | t3.xlarge | 5,849 | 2-3 days | ~$12-15 |
| 5 | t3.large | 5,849 | 3-4 days | ~$6-10 |
| 3 | t3.medium | 5,849 | 5-7 days | ~$8-12 |

**With API (OpenAI/Claude):**
- 10 workers: 1-2 days, ~$12 EC2 + $13 API = $25 total
- Much faster, higher success rate (99% vs 25%)

---

## 🔍 Troubleshooting

### Scraper stopped?
```bash
# Check if running
ps aux | grep python

# Check last errors
tail -100 logs/extractor.log | grep ERROR

# Restart if needed
cd ~/maharera-scraper
source venv/bin/activate
nohup python3 parallel_scraper.py --workers 10 --start-page 100 --pages 5749 --headless &
```

### Out of disk space?
```bash
# Check disk usage
df -h

# Clean up logs
rm logs/*.log.zip

# Increase storage: AWS Console → Volumes → Modify
```

### Browser crashes?
```bash
# Reduce workers
nohup python3 parallel_scraper.py --workers 5 --start-page 1 --pages 5849 --headless &
```

### Database locked errors?
```bash
# Already fixed in latest code with 30s timeout
# Just wait, it will retry automatically
```

---

## 🎯 Quick Command Reference

```bash
# SSH connect
ssh -i "maharera-key.pem" ubuntu@YOUR-IP

# Activate environment
cd ~/maharera-scraper && source venv/bin/activate

# Run scraper
nohup python3 parallel_scraper.py --workers 10 --start-page 1 --pages 5849 --headless &

# Monitor
tail -f logs/extractor.log

# Check stats
python3 check_db.py

# Export data
python3 main.py --export excel --output final

# Download (from Windows)
scp -i "maharera-key.pem" ubuntu@YOUR-IP:~/maharera-scraper/final.xlsx ./

# Stop instance
sudo shutdown -h now
```

---

## 💡 Pro Tips

1. **Use screen/tmux** for persistent sessions:
   ```bash
   sudo apt install screen
   screen -S scraper
   python3 parallel_scraper.py --workers 10 --start-page 1 --pages 5849 --headless
   # Ctrl+A then D to detach
   # screen -r scraper to reattach
   ```

2. **Backup database regularly:**
   ```bash
   # On EC2, run every 6 hours:
   cp data/agents.db data/agents_backup_$(date +%Y%m%d_%H%M%S).db
   ```

3. **Use CloudWatch** for monitoring:
   - AWS Console → CloudWatch → Alarms
   - Set alert if CPU > 90% for 10 minutes

4. **Take snapshots:**
   - EC2 → Volumes → Create Snapshot
   - In case something goes wrong

---

## 📞 Need Help?

Check logs:
```bash
tail -100 logs/extractor.log
python3 check_db.py
python3 captcha_stats.py
```

---

## ✅ Checklist

Before starting:
- [ ] EC2 instance running (t3.xlarge)
- [ ] SSH connection working
- [ ] aws_deploy.sh completed successfully
- [ ] Code uploaded to ~/maharera-scraper/
- [ ] .env file configured
- [ ] Test run successful (1 page)

During scraping:
- [ ] Monitor every few hours
- [ ] Check disk space (df -h)
- [ ] Verify data saving (python3 check_db.py)

After completion:
- [ ] Export to Excel
- [ ] Download all files to PC
- [ ] **STOP EC2 INSTANCE!**
- [ ] Verify downloaded data is complete

---

**🎉 You're ready to deploy! Your $100 AWS credits can easily handle this project.**

**Estimated final cost: $12-25** (you'll have $75-88 left!)
