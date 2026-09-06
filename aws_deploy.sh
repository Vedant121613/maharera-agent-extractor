#!/bin/bash
# AWS EC2 Deployment Script for MahaRERA Scraper
# For Ubuntu 22.04 on t3.xlarge (16GB RAM)

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  MahaRERA Scraper - AWS EC2 Deployment                  ║"
echo "║  Optimized for t3.xlarge (4 vCPU, 16GB RAM)             ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Update system
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install dependencies
echo "📦 Installing dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    tesseract-ocr \
    git \
    htop \
    tmux

# Verify Tesseract
echo "✅ Tesseract OCR version:"
tesseract --version

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python packages
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright Chromium..."
playwright install chromium
playwright install-deps chromium

# Create directories
echo "📁 Creating directories..."
mkdir -p data logs output

# Setup .env
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    
    # Update for AWS/Linux
    sed -i 's|HEADLESS=false|HEADLESS=true|g' .env
    sed -i 's|TESSERACT_CMD=.*|TESSERACT_CMD=/usr/bin/tesseract|g' .env
    
    echo "✅ .env created and configured for AWS"
else
    echo "ℹ️  .env already exists, skipping..."
fi

# Test database
echo "🗄️  Testing database..."
python3 -c "from database.database import Database; db = Database(); print('✅ Database OK')"

# Test Tesseract
echo "🔍 Testing Tesseract..."
python3 -c "import pytesseract; print('✅ Pytesseract OK')"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ Deployment Complete!                                 ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "📊 System Info:"
echo "  - CPU: $(nproc) cores"
echo "  - RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo "  - Disk: $(df -h . | awk 'NR==2 {print $4}') available"
echo ""
echo "🚀 Quick Start Commands:"
echo ""
echo "  # Test with 10 pages:"
echo "  python3 main.py --scrape --pages 10 --headless"
echo ""
echo "  # Run 10 workers (500 pages total):"
echo "  nohup python3 parallel_scraper.py --workers 10 --start-page 371 --pages 500 --headless > scraper.log 2>&1 &"
echo ""
echo "  # Monitor progress:"
echo "  python3 check_db.py"
echo "  tail -f logs/extractor.log"
echo ""
echo "  # View running processes:"
echo "  ps aux | grep python"
echo ""
echo "💡 Tips:"
echo "  - Use 'tmux' to keep sessions alive after disconnect"
echo "  - Monitor with: watch -n 30 'python3 check_db.py'"
echo "  - Stop AWS instance when done to save credits!"
echo ""
