#!/bin/bash
# Setup cron job for monthly S3 archiving
# This script installs a cron job that runs on the 1st of each month

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ARCHIVE_SCRIPT="$SCRIPT_DIR/monthly_archive.py"
OUTPUT_DIR="$SCRIPT_DIR/monthly-archives"
BUCKET_NAME="transaction-documents-demo-20251118"

# Log file
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/monthly-archive.log"

echo "=========================================="
echo "Monthly S3 Archive - Cron Setup"
echo "=========================================="
echo ""
echo "Script: $ARCHIVE_SCRIPT"
echo "Bucket: $BUCKET_NAME"
echo "Output: $OUTPUT_DIR"
echo "Log: $LOG_FILE"
echo ""

# Make script executable
chmod +x "$ARCHIVE_SCRIPT"

# Create the cron command
# Runs at 2:00 AM on the 1st of every month
CRON_TIME="0 2 1 * *"
CRON_CMD="$ARCHIVE_SCRIPT --bucket $BUCKET_NAME --output $OUTPUT_DIR --upload-to-s3 >> $LOG_FILE 2>&1"
CRON_ENTRY="$CRON_TIME $CRON_CMD"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$ARCHIVE_SCRIPT"; then
    echo "Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "$ARCHIVE_SCRIPT" | crontab -
fi

# Add new cron job
echo "Installing cron job..."
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo ""
echo "✓ Cron job installed successfully!"
echo ""
echo "Schedule: 2:00 AM on the 1st of every month"
echo ""
echo "To view cron jobs:"
echo "  crontab -l"
echo ""
echo "To remove this cron job:"
echo "  crontab -l | grep -v '$ARCHIVE_SCRIPT' | crontab -"
echo ""
echo "To test the script manually:"
echo "  $ARCHIVE_SCRIPT --bucket $BUCKET_NAME --output $OUTPUT_DIR"
echo ""
echo "To test with a specific date (e.g., archive October 2025):"
echo "  $ARCHIVE_SCRIPT --bucket $BUCKET_NAME --output $OUTPUT_DIR --date 2025-11-01"
echo ""
