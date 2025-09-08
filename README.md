# OSS Bucket Deletion Utility

A utility to delete all OSS buckets in your Alibaba Cloud account.

## Setup

1. **First time setup:** See [INSTALL.md](INSTALL.md) for Python installation on macOS

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Option 1: Using Environment Variables (Recommended)
```bash
# Set credentials
export ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret

# Activate virtual environment and run
source venv/bin/activate
python delete_oss_buckets.py
```

### Option 2: Command Line Arguments
```bash
source venv/bin/activate
python delete_oss_buckets.py <access_key_id> <access_key_secret>
```

The script will:
1. List all buckets with numbers
2. Allow you to select a specific bucket number to delete
3. Or choose option 0 to delete all buckets
4. Confirm before deletion

## Important Notes

- **⚠️ This operation is IRREVERSIBLE** - all bucket data will be permanently deleted
- **Lists buckets from ALL regions automatically** - no endpoint required
- Interactive selection - choose specific buckets or delete all
- Shows bucket region information
- Buckets are automatically emptied before deletion
- The script will prompt for confirmation before proceeding
- Each bucket's regional endpoint is automatically detected

## Access Points Limitation

**⚠️ IMPORTANT:** If buckets have **Access Points** configured, they must be deleted manually:

1. The script will skip buckets with access points and show a warning
2. Go to Alibaba Cloud Console → Object Storage Service (OSS)
3. Navigate to the bucket → Access Points
4. Delete all access points manually
5. Re-run the script to delete the bucket

## Security

- Never commit your access keys to version control
- Consider using environment variables or IAM roles for credentials
- Ensure your access key has OSS deletion permissions

