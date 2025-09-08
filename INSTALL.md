# Installation Guide (macOS)

## Install Python

### Option 1: Using Homebrew (Recommended)
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python
```

### Option 2: Download from Python.org
1. Go to https://www.python.org/downloads/
2. Download Python 3.8+ for macOS
3. Run the installer

## Setup Virtual Environment

```bash
# Navigate to project directory
cd /Users/ankitmehta/Documents/Alibabacloud

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Run the Script

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the script
python delete_oss_buckets.py <access_key_id> <access_key_secret> <endpoint>
```

## Verify Installation

```bash
# Check if oss2 is installed
python -c "import oss2; print('OSS2 installed successfully')"
```