# AWS RDS Option (PostgreSQL) - If You Want Cloud Database

**Note:** This is OPTIONAL. SQLite on EC2 works great for your use case!

## When to Use RDS:
- Multiple AWS instances scraping simultaneously
- Need to access data from different locations
- Want automatic backups
- Plan to build a web dashboard

## When to Stick with SQLite:
- ✅ **Single EC2 instance** (your current plan)
- ✅ **Temporary scraping** (download when done)
- ✅ **Save money** (RDS costs ~$15-20/month)
- ✅ **Simple setup** (no code changes)

---

## Setup RDS (PostgreSQL)

### 1. Create RDS Instance

**AWS Console → RDS → Create database:**
- Engine: PostgreSQL 15
- Template: Free tier (db.t3.micro) or Dev/Test (db.t3.small)
- Instance ID: `maharera-db`
- Master username: `maharera_admin`
- Master password: [your strong password]
- Storage: 20 GB
- Public access: **Yes** (or set up VPC properly)
- Security group: Allow PostgreSQL (5432) from your EC2 IP

**Cost:** ~$15-20/month (not free tier eligible long-term)

### 2. Update Dependencies

Add to `requirements.txt`:
```txt
psycopg2-binary==2.9.9
SQLAlchemy==2.0.23
```

### 3. Update .env

```env
# Database - PostgreSQL on RDS
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://maharera_admin:PASSWORD@maharera-db.xxxxx.us-east-1.rds.amazonaws.com:5432/maharera

# OR SQLite (current)
DATABASE_TYPE=sqlite
DB_PATH=data/agents.db
```

### 4. Update database.py

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.config import Config

# Check database type
if Config.DATABASE_TYPE == "postgresql":
    engine = create_engine(Config.DATABASE_URL)
else:
    # Current SQLite code
    engine = create_engine(f"sqlite:///{Config.DB_PATH}")

Session = sessionmaker(bind=engine)
```

### 5. Migrate Schema

```python
# Create tables in PostgreSQL
from database.models import Base
Base.metadata.create_all(engine)
```

### 6. Deploy

```bash
# On AWS EC2
source venv/bin/activate
pip install psycopg2-binary SQLAlchemy

# Run scraper (data goes to RDS now)
python3 parallel_scraper.py --workers 10 --start-page 371 --pages 500 --headless
```

---

## Advantages of RDS:

### 1. **No Download Needed**
- Data already in cloud
- Access from anywhere
- No scp/merge needed

### 2. **Multiple Workers**
- Run on multiple EC2 instances simultaneously
- All write to same database
- No conflicts

### 3. **Automatic Backups**
- Daily snapshots
- Point-in-time recovery
- No risk of losing data

### 4. **Easy to Query**
- Use any PostgreSQL client
- DBeaver, pgAdmin, etc.
- SQL queries from anywhere

---

## Disadvantages:

### 1. **Cost**
- **Free tier:** 750 hours/month (1 month only)
- **After free tier:** ~$15-20/month
- **Your use case:** Only need 2-3 days

### 2. **Network Latency**
- SQLite (local): 0.1ms
- RDS (network): 5-10ms
- Impact: ~10% slower

### 3. **Complexity**
- More setup
- Code changes needed
- Security groups, VPC, etc.

### 4. **Code Changes**
- Update database layer
- Handle PostgreSQL differences
- Test thoroughly

---

## Recommendation:

### ✅ **Use SQLite on EC2** (Current Setup)
**Because:**
- You have **1 EC2 instance**
- Scraping is **temporary** (2-3 days)
- Download is **easy** (1 command)
- **FREE** (no extra cost)
- **Works perfectly** for your scale

### ❌ **Skip RDS**
**Unless:**
- You need multiple EC2 instances
- You want a permanent cloud database
- You're building a web dashboard
- You need to access data 24/7

---

## Your Current Setup is Perfect!

**What happens on AWS:**
```
EC2 Instance (t3.xlarge)
├── Code: ~/maharera-agent-extractor/
├── Database: ~/maharera-agent-extractor/data/agents.db
├── Logs: ~/maharera-agent-extractor/logs/
└── Output: ~/maharera-agent-extractor/output/
```

**After scraping (2-3 days):**
```powershell
# Download from AWS to your PC
scp -i "key.pem" ubuntu@IP:~/maharera-agent-extractor/data/agents.db ./agents_aws.db

# Merge with local data
python merge_databases.py

# Result: Combined database on your PC
# Total: ~8,000-8,500 agents
```

**Then:**
- Stop AWS instance (save money!)
- All data safe on your PC
- Export to Excel whenever you want
- Restart AWS later if you need more pages

---

## Cost Comparison:

| Option | Setup | Monthly Cost | Total Cost (3 days) |
|--------|-------|--------------|---------------------|
| **SQLite on EC2** | ✅ Done | $0 (EC2 only) | **$12** |
| RDS | Need setup | $15-20 + EC2 | **$13.50 + $12** |

**Savings with SQLite:** $13.50 for 3 days scraping

---

## When to Consider RDS Later:

1. **Building a web app** to browse agents
2. **Running scraper 24/7** (continuous updates)
3. **Multiple developers** accessing data
4. **Need API** to query agents
5. **Permanent deployment** (not temporary scraping)

For now, **SQLite on EC2 is perfect!** 🎯
