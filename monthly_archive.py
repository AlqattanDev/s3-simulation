#!/usr/bin/env python3
"""
Monthly S3 Archive Script

Archives the previous month's files from S3 into separate ZIP files:
- One ZIP for Opening folder files
- One ZIP for Customer folder files

Can run as a cron job at the start of each month.
"""

import os
import sys
import zipfile
import tempfile
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
import argparse

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    print("Warning: boto3 not installed. S3 features will not be available.")
    print("Install with: pip install boto3")


class MonthlyArchiver:
    """Handle monthly archiving of S3 transaction documents."""

    def __init__(self, bucket_name, output_dir, use_s3=True, local_data_dir=None):
        """
        Initialize the archiver.

        Args:
            bucket_name: S3 bucket name
            output_dir: Local directory to save ZIP files
            use_s3: If True, use S3. If False, use local files
            local_data_dir: Path to local data directory (when use_s3=False)
        """
        self.bucket_name = bucket_name
        self.output_dir = Path(output_dir)
        self.use_s3 = use_s3
        self.local_data_dir = Path(local_data_dir) if local_data_dir else None

        if use_s3:
            if not HAS_BOTO3:
                raise RuntimeError("boto3 is required for S3 operations. Install with: pip install boto3")
            self.s3_client = boto3.client('s3')
        else:
            if not self.local_data_dir or not self.local_data_dir.exists():
                raise ValueError("local_data_dir must exist when use_s3=False")

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_previous_month_range(self, reference_date=None):
        """
        Get the start and end datetime for the previous month.

        Args:
            reference_date: Reference date (default: today)

        Returns:
            Tuple of (start_datetime, end_datetime) for previous month (UTC timezone-aware)
        """
        if reference_date is None:
            reference_date = datetime.now()

        # First day of current month
        first_of_current_month = reference_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Last day of previous month (one day before first of current month)
        last_of_previous_month = first_of_current_month - timedelta(days=1)

        # First day of previous month
        first_of_previous_month = last_of_previous_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # End of last day of previous month
        end_of_previous_month = first_of_current_month - timedelta(microseconds=1)

        # Make timezone-aware (UTC) for S3 compatibility
        if self.use_s3:
            first_of_previous_month = first_of_previous_month.replace(tzinfo=timezone.utc)
            end_of_previous_month = end_of_previous_month.replace(tzinfo=timezone.utc)

        return first_of_previous_month, end_of_previous_month

    def list_s3_files(self, prefix, start_date, end_date):
        """
        List S3 files in a prefix that fall within the date range.
        Uses object metadata 'original-timestamp' if available, otherwise falls back to LastModified.

        Args:
            prefix: S3 prefix (folder path)
            start_date: Start datetime
            end_date: End datetime

        Returns:
            List of S3 object keys
        """
        files = []
        paginator = self.s3_client.get_paginator('list_objects_v2')

        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            if 'Contents' not in page:
                continue

            for obj in page['Contents']:
                # Get object metadata to check for original-timestamp
                try:
                    head_response = self.s3_client.head_object(
                        Bucket=self.bucket_name,
                        Key=obj['Key']
                    )
                    metadata = head_response.get('Metadata', {})

                    # Use original-timestamp from metadata if available
                    if 'original-timestamp' in metadata:
                        # Parse the timestamp (format: YYYY-MM-DDTHH:MM:SS)
                        timestamp_str = metadata['original-timestamp']
                        file_date = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
                        # Make timezone-aware for comparison
                        file_date = file_date.replace(tzinfo=timezone.utc)
                    else:
                        # Fall back to LastModified
                        file_date = obj['LastModified']

                    # Check if file's date is within our range
                    if start_date <= file_date <= end_date:
                        files.append(obj['Key'])

                except Exception as e:
                    # If metadata read fails, fall back to LastModified
                    if start_date <= obj['LastModified'] <= end_date:
                        files.append(obj['Key'])

        return files

    def list_local_files(self, folder_name, start_date, end_date):
        """
        List local files that fall within the date range.

        Args:
            folder_name: Folder name (Opening or Customer)
            start_date: Start datetime
            end_date: End datetime

        Returns:
            List of file paths relative to data directory
        """
        files = []
        folder_path = self.local_data_dir / folder_name

        if not folder_path.exists():
            return files

        for file_path in folder_path.rglob('*'):
            if file_path.is_file():
                # Get file modification time
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                if start_date <= mtime <= end_date:
                    # Get relative path from data directory
                    rel_path = file_path.relative_to(self.local_data_dir)
                    files.append(str(rel_path))

        return files

    def download_s3_file(self, s3_key, local_path):
        """Download a file from S3."""
        local_path.parent.mkdir(parents=True, exist_ok=True)
        self.s3_client.download_file(self.bucket_name, s3_key, str(local_path))

    def create_zip_archive(self, files, zip_path, folder_prefix, temp_dir):
        """
        Create a ZIP archive from a list of files.

        Args:
            files: List of file keys/paths
            zip_path: Output ZIP file path
            folder_prefix: S3 prefix to filter by (e.g., "Opening/")
            temp_dir: Temporary directory for downloads
        """
        if not files:
            print(f"  No files found for {folder_prefix} - skipping ZIP creation")
            return 0

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_key in files:
                if self.use_s3:
                    # Download from S3 to temp dir
                    local_file = Path(temp_dir) / file_key
                    self.download_s3_file(file_key, local_file)
                else:
                    # Use local file
                    local_file = self.local_data_dir / file_key

                # Add to ZIP with original path structure
                zipf.write(local_file, arcname=file_key)

        return len(files)

    def archive_previous_month(self, reference_date=None, upload_to_s3=False):
        """
        Archive the previous month's files into separate ZIP files.

        Args:
            reference_date: Reference date (default: today)
            upload_to_s3: If True, upload ZIP files back to S3

        Returns:
            Dict with statistics
        """
        start_date, end_date = self.get_previous_month_range(reference_date)

        # Format for filenames: YYYY-MM (previous month)
        month_str = start_date.strftime('%Y-%m')

        print("=" * 70)
        print(f"Monthly Archive - {month_str}")
        print("=" * 70)
        print(f"Date range: {start_date.strftime('%Y-%m-%d %H:%M:%S')} to {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Source: {'S3 bucket: ' + self.bucket_name if self.use_s3 else 'Local: ' + str(self.local_data_dir)}")
        print(f"Output: {self.output_dir}")
        print()

        stats = {
            'month': month_str,
            'opening_files': 0,
            'customer_files': 0,
            'opening_zip': None,
            'customer_zip': None
        }

        # Create temporary directory for downloads
        with tempfile.TemporaryDirectory() as temp_dir:

            # Process Opening folder
            print("Processing Opening folder...")
            if self.use_s3:
                opening_files = self.list_s3_files('Opening/', start_date, end_date)
            else:
                opening_files = self.list_local_files('Opening', start_date, end_date)

            print(f"  Found {len(opening_files)} files")

            if opening_files:
                opening_zip_name = f"Opening_{month_str}.zip"
                opening_zip_path = self.output_dir / opening_zip_name
                files_count = self.create_zip_archive(opening_files, opening_zip_path, 'Opening/', temp_dir)
                stats['opening_files'] = files_count
                stats['opening_zip'] = str(opening_zip_path)

                zip_size = opening_zip_path.stat().st_size
                print(f"  Created: {opening_zip_name} ({self.format_size(zip_size)}, {files_count} files)")

            # Process Customer folder
            print("\nProcessing Customer folder...")
            if self.use_s3:
                customer_files = self.list_s3_files('Customer/', start_date, end_date)
            else:
                customer_files = self.list_local_files('Customer', start_date, end_date)

            print(f"  Found {len(customer_files)} files")

            if customer_files:
                customer_zip_name = f"Customer_{month_str}.zip"
                customer_zip_path = self.output_dir / customer_zip_name
                files_count = self.create_zip_archive(customer_files, customer_zip_path, 'Customer/', temp_dir)
                stats['customer_files'] = files_count
                stats['customer_zip'] = str(customer_zip_path)

                zip_size = customer_zip_path.stat().st_size
                print(f"  Created: {customer_zip_name} ({self.format_size(zip_size)}, {files_count} files)")

        # Upload to S3 if requested
        if upload_to_s3 and self.use_s3:
            print("\nUploading ZIP files to S3...")
            archive_prefix = "archives/"

            if stats['opening_zip']:
                s3_key = archive_prefix + Path(stats['opening_zip']).name
                self.s3_client.upload_file(stats['opening_zip'], self.bucket_name, s3_key)
                print(f"  Uploaded: s3://{self.bucket_name}/{s3_key}")

            if stats['customer_zip']:
                s3_key = archive_prefix + Path(stats['customer_zip']).name
                self.s3_client.upload_file(stats['customer_zip'], self.bucket_name, s3_key)
                print(f"  Uploaded: s3://{self.bucket_name}/{s3_key}")

        # Summary
        print("\n" + "=" * 70)
        print("Archive Complete!")
        print("=" * 70)
        print(f"Month: {month_str}")
        print(f"Opening files: {stats['opening_files']}")
        print(f"Customer files: {stats['customer_files']}")
        print(f"Total files: {stats['opening_files'] + stats['customer_files']}")

        if stats['opening_zip']:
            print(f"\nOpening archive: {stats['opening_zip']}")
        if stats['customer_zip']:
            print(f"Customer archive: {stats['customer_zip']}")

        return stats

    @staticmethod
    def format_size(size_bytes):
        """Format bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Archive previous month S3 files into ZIP folders',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Archive from S3 bucket
  %(prog)s --bucket my-bucket --output ./archives

  # Archive from local files (for testing)
  %(prog)s --local-dir ./data --output ./archives

  # Archive and upload ZIPs back to S3
  %(prog)s --bucket my-bucket --output ./archives --upload-to-s3

  # Test with a specific reference date
  %(prog)s --bucket my-bucket --output ./archives --date 2025-10-15
        """
    )

    parser.add_argument('--bucket', help='S3 bucket name')
    parser.add_argument('--local-dir', help='Local data directory (for testing without S3)')
    parser.add_argument('--output', required=True, help='Output directory for ZIP files')
    parser.add_argument('--upload-to-s3', action='store_true',
                       help='Upload ZIP files back to S3 in archives/ folder')
    parser.add_argument('--date', help='Reference date (YYYY-MM-DD) for testing (default: today)')

    args = parser.parse_args()

    # Validate arguments
    if not args.bucket and not args.local_dir:
        parser.error('Either --bucket or --local-dir must be specified')

    if args.bucket and args.local_dir:
        parser.error('Cannot specify both --bucket and --local-dir')

    # Parse reference date if provided
    reference_date = None
    if args.date:
        try:
            reference_date = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            parser.error(f'Invalid date format: {args.date}. Use YYYY-MM-DD')

    # Create archiver
    use_s3 = bool(args.bucket)
    archiver = MonthlyArchiver(
        bucket_name=args.bucket if use_s3 else 'local',
        output_dir=args.output,
        use_s3=use_s3,
        local_data_dir=args.local_dir
    )

    # Run archive
    try:
        archiver.archive_previous_month(
            reference_date=reference_date,
            upload_to_s3=args.upload_to_s3
        )
        return 0
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
