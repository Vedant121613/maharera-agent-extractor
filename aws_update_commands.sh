#!/bin/bash
# AWS Update and Deploy Script
# Run this on your AWS EC2 instance after connecting via SSH

echo "================================================"
echo "  MahaRERA Scraper - AWS Update Script"
echo "================================================"

# Navigate to project directory
echo "1. Navigating to project directory..."
cd ~/maharera-agent-extractor || { echo "Error: Project directory not found"; exit 1; }

# Check current status
echo "2. Checking git status..."
git status

# Stash any local changes
echo "3. Stashing local changes (if any)..."
git stash

# Pull latest code
echo "4. Pulling latest code from GitHub..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "Error: Git pull failed"
    exit 1
fi

# Show latest commits
echo "5. Latest commits:"
git log --oneline -n 5

# Activate virtual environment
echo "6. Activating virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment"
    exit 1
fi

# Update dependencies
echo "7. Updating dependencies..."
pip install -r requirements.txt --upgrade --quiet

# Verify Playwright
echo "8. Verifying Playwright..."
playwright --version

# Check database
echo "9. Checking database status..."
python check_db.py

echo ""
echo "================================================"
echo "  ✅ Update Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Test: python parallel_scraper.py --workers 1 --start-page 1 --pages 3"
echo "  2. Run:  nohup python parallel_scraper.py --workers 3 --start-page 1 --pages 500 > scraper.log 2>&1 &"
echo "  3. Monitor: tail -f scraper.log"
echo ""
