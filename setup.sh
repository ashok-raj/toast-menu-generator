#!/bin/bash

# Toast Menu Generator Setup Script
# This script sets up the Python virtual environment and installs dependencies

set -e  # Exit on any error

echo "🍞 Toast Menu Generator Setup"
echo "================================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env template..."
    cat > .env << 'EOF'
# Toast API Configuration
TOAST_HOSTNAME=ws-sandbox-api.toasttab.com
TOAST_CLIENT_ID=your_client_id_here
TOAST_CLIENT_SECRET=your_client_secret_here
TOAST_RESTAURANT_GUID=your_restaurant_guid_here

# Optional: Set to 'production' for live API
# TOAST_ENVIRONMENT=sandbox
EOF
    echo "✅ .env template created - please edit with your Toast API credentials"
else
    echo "✅ .env file already exists"
fi

# Check if emp.guids file exists
if [ ! -f "emp.guids" ]; then
    echo "👥 Creating emp.guids template..."
    cat > emp.guids << 'EOF'
# Add employee GUIDs here, one per line
# You can get these by running: python emptime.py
# Example:
# a1b2c3d4-e5f6-7890-abcd-ef1234567890
# b2c3d4e5-f6g7-8901-bcde-f23456789012
EOF
    echo "✅ emp.guids template created - add employee GUIDs here"
else
    echo "✅ emp.guids file already exists"
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x emptime.py
chmod +x sales.py
if [ -f "main.py" ]; then
    chmod +x main.py
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Toast API credentials"
echo "2. Get employee list: python emptime.py"
echo "3. Add employee GUIDs to emp.guids file"
echo "4. Run time logs: python emptime.py -t"
echo "5. Run sales reports: python sales.py -s YYYY-MM-DD -e YYYY-MM-DD"
echo ""
echo "To activate the virtual environment later, run:"
echo "source venv/bin/activate"
echo ""
echo "To deactivate when done:"
echo "deactivate"