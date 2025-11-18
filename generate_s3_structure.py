#!/usr/bin/env python3
"""
Generate S3 bucket structure with simulated transaction documents.
Creates 3 months of data for Opening and Customer folders.
"""

import os
import random
import string
from datetime import datetime, timedelta
import subprocess
import sys

# Configuration
BUCKET_NAME = "transaction-documents-demo-20251118"
LOCAL_BASE_DIR = "/home/ali/s3-test/data"
MONTHS_TO_SIMULATE = 3

# Opening folder: 6000 deposits/year = 500/month
TRANSACTIONS_PER_MONTH = 500

# Customer folder: 300 documents/year = 25/month
CUSTOMER_DOCS_PER_MONTH = 25

# File specifications for Opening folder
OPENING_FILE_SPECS = {
    "IDD.pdf": 620 * 1024,      # 620 KB
    "KYC.pdf": 1300 * 1024,     # 1300 KB
    "OPA.xml": 4 * 1024,        # 4 KB
    "PID.pdf": 300 * 1024       # 300 KB
}

# Customer file specs: 300-1300 KB
CUSTOMER_FILE_MIN_SIZE = 300 * 1024
CUSTOMER_FILE_MAX_SIZE = 1300 * 1024


def create_dummy_pdf(filepath, size_bytes):
    """Create a dummy PDF file with specified size."""
    # PDF header
    pdf_header = b"%PDF-1.4\n"
    # PDF minimal structure
    pdf_content = b"""1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources 4 0 R /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >>
endobj
5 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Dummy Document) Tj ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000229 00000 n
0000000327 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
420
%%EOF
"""

    # Calculate padding needed
    header_size = len(pdf_header) + len(pdf_content)
    padding_size = max(0, size_bytes - header_size)

    # Create padding with random data
    padding = b'\x00' * padding_size

    # Write file
    with open(filepath, 'wb') as f:
        f.write(pdf_header)
        f.write(pdf_content)
        f.write(padding)


def create_dummy_xml(filepath, size_bytes):
    """Create a dummy XML file with specified size."""
    xml_header = b'<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_start = b'<document>\n  <type>OPA</type>\n  <data>\n'
    xml_end = b'  </data>\n</document>\n'

    # Calculate padding needed
    header_size = len(xml_header) + len(xml_start) + len(xml_end)
    padding_size = max(0, size_bytes - header_size)

    # Create padding with random text
    padding = ''.join(random.choices(string.ascii_letters + string.digits + ' \n', k=padding_size))

    # Write file
    with open(filepath, 'wb') as f:
        f.write(xml_header)
        f.write(xml_start)
        f.write(padding.encode('utf-8'))
        f.write(xml_end)


def generate_transaction_id():
    """Generate a random transaction ID."""
    return f"TXN{random.randint(100000, 999999)}"


def generate_opening_folder(base_dir, start_date, end_date):
    """Generate Opening folder structure with transactions."""
    opening_dir = os.path.join(base_dir, "Opening")
    os.makedirs(opening_dir, exist_ok=True)

    # Calculate number of transactions
    days = (end_date - start_date).days
    total_transactions = TRANSACTIONS_PER_MONTH * MONTHS_TO_SIMULATE

    print(f"Generating {total_transactions} transactions in Opening folder...")

    transaction_count = 0
    for i in range(total_transactions):
        # Generate transaction ID
        txn_id = generate_transaction_id()
        txn_dir = os.path.join(opening_dir, txn_id)
        os.makedirs(txn_dir, exist_ok=True)

        # Create each file
        for filename, size in OPENING_FILE_SPECS.items():
            filepath = os.path.join(txn_dir, filename)

            if filename.endswith('.xml'):
                create_dummy_xml(filepath, size)
            else:  # PDF
                create_dummy_pdf(filepath, size)

        transaction_count += 1
        if transaction_count % 100 == 0:
            print(f"  Created {transaction_count}/{total_transactions} transactions")

    print(f"✓ Opening folder complete: {total_transactions} transactions")
    return total_transactions


def generate_customer_folder(base_dir, start_date, end_date):
    """Generate Customer folder with various documents."""
    customer_dir = os.path.join(base_dir, "Customer")
    os.makedirs(customer_dir, exist_ok=True)

    total_docs = CUSTOMER_DOCS_PER_MONTH * MONTHS_TO_SIMULATE

    print(f"Generating {total_docs} documents in Customer folder...")

    for i in range(total_docs):
        # Randomly choose PDF or XML (70% PDF, 30% XML)
        file_ext = "pdf" if random.random() < 0.7 else "xml"

        # Generate filename with timestamp
        doc_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
        filename = f"CUST_{doc_date.strftime('%Y%m%d')}_{random.randint(1000, 9999)}.{file_ext}"
        filepath = os.path.join(customer_dir, filename)

        # Random size between 300-1300 KB
        size = random.randint(CUSTOMER_FILE_MIN_SIZE, CUSTOMER_FILE_MAX_SIZE)

        if file_ext == 'xml':
            create_dummy_xml(filepath, size)
        else:
            create_dummy_pdf(filepath, size)

    print(f"✓ Customer folder complete: {total_docs} documents")
    return total_docs


def upload_to_s3(local_dir, bucket_name):
    """Upload local directory to S3 bucket."""
    print(f"\nUploading to S3 bucket: {bucket_name}")

    cmd = [
        "aws", "s3", "sync",
        local_dir,
        f"s3://{bucket_name}/",
        "--quiet"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✓ Upload complete!")
    else:
        print(f"✗ Upload failed: {result.stderr}")
        return False

    return True


def get_folder_size(folder_path):
    """Calculate total size of a folder."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
    return total_size


def format_size(size_bytes):
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def main():
    """Main execution function."""
    print("=" * 60)
    print("S3 Transaction Document Structure Generator")
    print("=" * 60)
    print(f"Bucket: {BUCKET_NAME}")
    print(f"Simulating {MONTHS_TO_SIMULATE} months of data")
    print(f"Local staging: {LOCAL_BASE_DIR}")
    print("=" * 60)

    # Calculate date range (last 3 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=MONTHS_TO_SIMULATE * 30)

    print(f"\nDate range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

    # Clean and create local directory
    if os.path.exists(LOCAL_BASE_DIR):
        print(f"\nCleaning existing directory: {LOCAL_BASE_DIR}")
        subprocess.run(["rm", "-rf", LOCAL_BASE_DIR])

    os.makedirs(LOCAL_BASE_DIR, exist_ok=True)

    # Generate folders
    print("\n" + "=" * 60)
    print("GENERATING LOCAL FILES")
    print("=" * 60)

    opening_count = generate_opening_folder(LOCAL_BASE_DIR, start_date, end_date)
    customer_count = generate_customer_folder(LOCAL_BASE_DIR, start_date, end_date)

    # Calculate statistics
    opening_size = get_folder_size(os.path.join(LOCAL_BASE_DIR, "Opening"))
    customer_size = get_folder_size(os.path.join(LOCAL_BASE_DIR, "Customer"))
    total_size = opening_size + customer_size

    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    print(f"Opening folder:")
    print(f"  - Transactions: {opening_count}")
    print(f"  - Files: {opening_count * 4}")
    print(f"  - Total size: {format_size(opening_size)}")
    print(f"\nCustomer folder:")
    print(f"  - Documents: {customer_count}")
    print(f"  - Total size: {format_size(customer_size)}")
    print(f"\nOverall:")
    print(f"  - Total files: {opening_count * 4 + customer_count}")
    print(f"  - Total size: {format_size(total_size)}")

    # Upload to S3
    print("\n" + "=" * 60)
    print("UPLOADING TO S3")
    print("=" * 60)

    success = upload_to_s3(LOCAL_BASE_DIR, BUCKET_NAME)

    if success:
        print("\n" + "=" * 60)
        print("✓ SUCCESS - S3 bucket structure created!")
        print("=" * 60)
        print(f"\nView bucket contents:")
        print(f"  aws s3 ls s3://{BUCKET_NAME}/ --recursive --human-readable --summarize")
        print(f"\nBucket URL:")
        print(f"  https://s3.console.aws.amazon.com/s3/buckets/{BUCKET_NAME}")
    else:
        print("\n✗ Upload failed - check error messages above")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
