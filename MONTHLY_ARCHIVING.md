# Monthly Archiving for S3 Transaction Documents

This document explains how to automatically archive previous month's files into separate ZIP folders.

## Overview

The `monthly_archive.py` script automatically:
- Identifies all files from the previous month (based on last modified date)
- Creates separate ZIP archives for Opening and Customer folders
- Optionally uploads the ZIP files back to S3 for long-term storage
- Can be scheduled to run automatically on the 1st of each month

## Features

- **Automatic Date Detection**: Automatically determines the previous month's date range
- **Separate Archives**: Creates one ZIP for Opening folder, one for Customer folder
- **S3 or Local**: Works with S3 buckets or local file systems (for testing)
- **Upload to S3**: Optionally uploads generated ZIPs to `archives/` folder in S3
- **Cron Ready**: Can be scheduled as a cron job for automation
- **Testing**: Supports custom dates for testing past months

## Installation

### Prerequisites

For S3 functionality:
```bash
pip install boto3
```

For local testing (no dependencies needed):
```bash
# Works with standard Python libraries
```

### AWS Credentials

Ensure AWS credentials are configured:
```bash
aws configure
```

Or set environment variables:
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

## Usage

### Basic Usage - Archive from S3

Archive the previous month's files from S3:

```bash
python3 monthly_archive.py --bucket transaction-documents-demo-20251118 --output ./archives
```

### Upload Archives Back to S3

Archive and upload the ZIPs back to S3 in the `archives/` folder:

```bash
python3 monthly_archive.py \
    --bucket transaction-documents-demo-20251118 \
    --output ./archives \
    --upload-to-s3
```

### Test with Local Files

Test the script with local files (no S3 needed):

```bash
python3 monthly_archive.py \
    --local-dir ./data \
    --output ./archives
```

### Test with Specific Date

Archive files for a specific month (useful for testing):

```bash
# Archive October 2025 files (run this on any date in November or later)
python3 monthly_archive.py \
    --bucket transaction-documents-demo-20251118 \
    --output ./archives \
    --date 2025-11-01
```

## Output

The script creates ZIP files with the naming pattern:

```
archives/
├── Opening_2025-10.zip      # All Opening folder files from October 2025
└── Customer_2025-10.zip     # All Customer folder files from October 2025
```

Each ZIP maintains the original folder structure:

**Opening_2025-10.zip:**
```
Opening/
├── TXN101557/
│   ├── IDD.pdf
│   ├── KYC.pdf
│   ├── OPA.xml
│   └── PID.pdf
├── TXN101582/
│   ├── IDD.pdf
│   └── ...
```

**Customer_2025-10.zip:**
```
Customer/
├── CUST_20251001_1234.pdf
├── CUST_20251005_5678.pdf
└── ...
```

## Automation with Cron

### Automatic Setup

Use the provided setup script to install a cron job:

```bash
chmod +x setup_monthly_cron.sh
./setup_monthly_cron.sh
```

This installs a cron job that runs at **2:00 AM on the 1st of every month**.

### Manual Cron Setup

Alternatively, manually add to crontab:

```bash
crontab -e
```

Add this line:
```
# Archive previous month at 2:00 AM on the 1st of each month
0 2 1 * * /path/to/monthly_archive.py --bucket transaction-documents-demo-20251118 --output /path/to/archives --upload-to-s3 >> /path/to/logs/archive.log 2>&1
```

### View Installed Cron Jobs

```bash
crontab -l
```

### Remove Cron Job

```bash
crontab -l | grep -v 'monthly_archive.py' | crontab -
```

## AWS Lambda Alternative

For a serverless approach, you can deploy this as an AWS Lambda function triggered by EventBridge (CloudWatch Events).

### Lambda Function Setup

1. **Create Lambda Function**:
   - Runtime: Python 3.11
   - Handler: `monthly_archive.lambda_handler`

2. **Add EventBridge Trigger**:
   - Schedule expression: `cron(0 2 1 * ? *)` (2 AM on 1st of each month)

3. **IAM Permissions**:
   The Lambda function needs these permissions:
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "s3:ListBucket",
                   "s3:GetObject",
                   "s3:PutObject"
               ],
               "Resource": [
                   "arn:aws:s3:::transaction-documents-demo-20251118",
                   "arn:aws:s3:::transaction-documents-demo-20251118/*"
               ]
           }
       ]
   }
   ```

4. **Increase Timeout**: Set to at least 5 minutes (adjust based on data volume)

5. **Increase Memory**: Set to at least 512 MB

## Command-Line Options

```
--bucket BUCKET         S3 bucket name
--local-dir DIR         Local data directory (for testing without S3)
--output DIR            Output directory for ZIP files (required)
--upload-to-s3          Upload ZIP files back to S3 in archives/ folder
--date YYYY-MM-DD       Reference date for testing (default: today)
```

## Examples

### Monthly Production Run

Run at the start of each month to archive the previous month:

```bash
python3 monthly_archive.py \
    --bucket transaction-documents-demo-20251118 \
    --output /backups/monthly-archives \
    --upload-to-s3
```

### Test October 2025 Archive

```bash
python3 monthly_archive.py \
    --bucket transaction-documents-demo-20251118 \
    --output ./test-archives \
    --date 2025-11-01
```

### Local Testing

```bash
# First generate test data
python3 generate_s3_structure.py

# Then archive locally
python3 monthly_archive.py \
    --local-dir ./data \
    --output ./test-archives \
    --date 2025-11-01
```

## Sample Output

```
======================================================================
Monthly Archive - 2025-10
======================================================================
Date range: 2025-10-01 00:00:00 to 2025-10-31 23:59:59
Source: S3 bucket: transaction-documents-demo-20251118
Output: ./archives

Processing Opening folder...
  Found 500 files
  Created: Opening_2025-10.zip (1.06 GB, 500 files)

Processing Customer folder...
  Found 25 files
  Created: Customer_2025-10.zip (18.2 MB, 25 files)

Uploading ZIP files to S3...
  Uploaded: s3://transaction-documents-demo-20251118/archives/Opening_2025-10.zip
  Uploaded: s3://transaction-documents-demo-20251118/archives/Customer_2025-10.zip

======================================================================
Archive Complete!
======================================================================
Month: 2025-10
Opening files: 500
Customer files: 25
Total files: 525

Opening archive: ./archives/Opening_2025-10.zip
Customer archive: ./archives/Customer_2025-10.zip
```

## File Selection Logic

Files are selected based on their **Last Modified** timestamp in S3 (or filesystem):

- **Start**: First day of previous month at 00:00:00
- **End**: Last day of previous month at 23:59:59

For example, when run on **December 1, 2025**:
- Archives files from **November 1, 2025 00:00:00** to **November 30, 2025 23:59:59**

## Storage Optimization

### S3 Lifecycle Policy

After archiving to ZIP files, you can apply S3 lifecycle policies to:

1. **Move old ZIPs to Glacier**: Archive ZIPs older than 30 days to S3 Glacier
2. **Delete original files**: After successful archiving, delete individual files older than 90 days
3. **Version retention**: Keep only recent versions

Example lifecycle policy:
```json
{
    "Rules": [
        {
            "Id": "ArchiveOldZips",
            "Status": "Enabled",
            "Prefix": "archives/",
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "GLACIER"
                }
            ]
        }
    ]
}
```

## Monitoring

### Check Cron Logs

```bash
tail -f logs/monthly-archive.log
```

### CloudWatch (for Lambda)

Monitor Lambda execution in CloudWatch Logs:
- Function duration
- Memory usage
- Errors and exceptions

### Email Notifications

Add email notifications by piping cron output:

```bash
0 2 1 * * /path/to/monthly_archive.py ... 2>&1 | mail -s "Monthly Archive Complete" admin@example.com
```

## Troubleshooting

### Issue: "boto3 not installed"

```bash
pip install boto3
```

### Issue: "Access Denied" when accessing S3

Check AWS credentials and IAM permissions:
```bash
aws s3 ls s3://transaction-documents-demo-20251118/
```

### Issue: No files found for previous month

- Verify files exist in S3 with correct timestamps
- Test with a specific date: `--date 2025-11-01`
- Check date range in output

### Issue: Cron job not running

- Check cron logs: `grep CRON /var/log/syslog`
- Verify script is executable: `chmod +x monthly_archive.py`
- Test script manually first

## Best Practices

1. **Test First**: Always test with `--local-dir` and `--date` before running on production
2. **Monitor Logs**: Keep logs of all archive runs
3. **Verify ZIPs**: Periodically verify ZIP integrity
4. **Backup Strategy**: Keep ZIPs in S3 with Glacier backup
5. **Retention Policy**: Define how long to keep ZIPs (e.g., 7 years for compliance)
6. **Alerting**: Set up alerts if archiving fails

## Integration with Existing Workflows

### Backup Verification

After archiving, verify ZIP contents:

```bash
# List contents
unzip -l archives/Opening_2025-10.zip

# Extract to verify
unzip -t archives/Opening_2025-10.zip
```

### Audit Trail

Maintain an audit log of all archives:

```bash
python3 monthly_archive.py ... 2>&1 | tee -a audit.log
```

## Summary

The monthly archiving solution provides:

✅ **Automated**: Set and forget with cron or Lambda
✅ **Organized**: Separate ZIPs for each folder
✅ **Reliable**: Based on file modification timestamps
✅ **Testable**: Local mode and custom dates for testing
✅ **Scalable**: Works with thousands of files
✅ **Cost-Effective**: Compress and archive to cheaper storage tiers

This ensures your S3 bucket stays organized while maintaining efficient long-term storage of historical documents.
