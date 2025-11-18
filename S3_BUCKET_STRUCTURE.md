# S3 Bucket Structure - Transaction Documents

**Bucket Name:** `transaction-documents-demo-20251118`

**Region:** Current AWS region

**Date Range:** August 20, 2025 - November 18, 2025 (3 months)

---

## Overview Statistics

| Metric | Value |
|--------|-------|
| **Total Files** | 6,075 |
| **Total Size** | 3.23 GB |
| **Opening Transactions** | 1,500 |
| **Opening Files** | 6,000 (4 per transaction) |
| **Opening Size** | 3.18 GB |
| **Customer Documents** | 75 |
| **Customer Size** | 54.69 MB |

---

## Folder Structure Tree

```
transaction-documents-demo-20251118/
│
├── Opening/                                    [1,500 transactions, 6,000 files, 3.18 GB]
│   │
│   ├── TXN101557/                             [Transaction folder]
│   │   ├── IDD.pdf                            [620 KB - Identity Document]
│   │   ├── KYC.pdf                            [1.3 MB - Know Your Customer]
│   │   ├── OPA.xml                            [4 KB - Opening Agreement]
│   │   └── PID.pdf                            [300 KB - Personal ID]
│   │
│   ├── TXN101582/                             [Transaction folder]
│   │   ├── IDD.pdf                            [620 KB]
│   │   ├── KYC.pdf                            [1.3 MB]
│   │   ├── OPA.xml                            [4 KB]
│   │   └── PID.pdf                            [300 KB]
│   │
│   ├── TXN101737/                             [Transaction folder]
│   │   ├── IDD.pdf                            [620 KB]
│   │   ├── KYC.pdf                            [1.3 MB]
│   │   ├── OPA.xml                            [4 KB]
│   │   └── PID.pdf                            [300 KB]
│   │
│   ├── TXN104102/                             [Transaction folder]
│   │   ├── IDD.pdf                            [620 KB]
│   │   ├── KYC.pdf                            [1.3 MB]
│   │   ├── OPA.xml                            [4 KB]
│   │   └── PID.pdf                            [300 KB]
│   │
│   ├── TXN104150/                             [Transaction folder]
│   │   ├── IDD.pdf                            [620 KB]
│   │   ├── KYC.pdf                            [1.3 MB]
│   │   ├── OPA.xml                            [4 KB]
│   │   └── PID.pdf                            [300 KB]
│   │
│   ├── ... [1,495 more transaction folders]
│   │
│   └── TXN999845/                             [Transaction folder]
│       ├── IDD.pdf                            [620 KB]
│       ├── KYC.pdf                            [1.3 MB]
│       ├── OPA.xml                            [4 KB]
│       └── PID.pdf                            [300 KB]
│
└── Customer/                                   [75 documents, 54.69 MB]
    │
    ├── CUST_20250820_4815.pdf                 [323 KB]
    ├── CUST_20250820_9711.pdf                 [501 KB]
    ├── CUST_20250822_4257.pdf                 [342 KB]
    ├── CUST_20250823_4894.pdf                 [1.09 MB]
    ├── CUST_20250826_9466.pdf                 [566 KB]
    ├── CUST_20250828_7160.xml                 [812 KB]
    ├── CUST_20250829_7132.pdf                 [1.14 MB]
    ├── CUST_20250830_8839.pdf                 [826 KB]
    ├── ... [67 more customer documents]
    └── CUST_20251116_9842.pdf                 [~500 KB - 1.2 MB range]
```

---

## Detailed Breakdown

### Opening Folder

**Purpose:** New account opening documents
**Expected Volume:** 6,000 deposits/year (~500/month)
**Current Data:** 3 months = 1,500 transactions

#### File Structure Per Transaction

Each transaction folder (e.g., `TXN101557/`) contains exactly 4 files:

| File | Type | Size | Description |
|------|------|------|-------------|
| `IDD.pdf` | PDF | 620 KB | Identity Document |
| `KYC.pdf` | PDF | 1.3 MB | Know Your Customer Documentation |
| `OPA.xml` | XML | 4 KB | Opening Agreement (structured data) |
| `PID.pdf` | PDF | 300 KB | Personal Identification |

**Total per transaction:** 2.22 MB (4 files)

#### Naming Convention

- **Pattern:** `TXN######` (6 random digits)
- **Examples:**
  - `TXN101557`
  - `TXN234891`
  - `TXN999845`

#### Monthly Growth

| Month | Transactions | Files | Size |
|-------|-------------|-------|------|
| Month 1 | 500 | 2,000 | 1.06 GB |
| Month 2 | 500 | 2,000 | 1.06 GB |
| Month 3 | 500 | 2,000 | 1.06 GB |
| **Total (3 months)** | **1,500** | **6,000** | **3.18 GB** |
| **Projected (1 year)** | **6,000** | **24,000** | **12.72 GB** |

---

### Customer Folder

**Purpose:** General customer documents and correspondence
**Expected Volume:** 300 documents/year (~25/month)
**Current Data:** 3 months = 75 documents

#### File Characteristics

| Attribute | Details |
|-----------|---------|
| **File Types** | PDF (70%), XML (30%) |
| **Size Range** | 300 KB - 1.3 MB |
| **Average Size** | ~730 KB |

#### Naming Convention

- **Pattern:** `CUST_YYYYMMDD_####.ext`
- **Components:**
  - `CUST_`: Prefix
  - `YYYYMMDD`: Date (e.g., 20250820)
  - `####`: 4-digit random number
  - `.ext`: Extension (pdf or xml)

#### Examples

```
CUST_20250820_4815.pdf  → Document from August 20, 2025
CUST_20250828_7160.xml  → XML document from August 28, 2025
CUST_20251116_9842.pdf  → Document from November 16, 2025
```

#### Monthly Growth

| Month | Documents | Size |
|-------|-----------|------|
| Month 1 | 25 | ~18 MB |
| Month 2 | 25 | ~18 MB |
| Month 3 | 25 | ~18 MB |
| **Total (3 months)** | **75** | **54.69 MB** |
| **Projected (1 year)** | **300** | **~220 MB** |

---

## Storage Growth Projections

### Yearly Projections

| Folder | Files/Year | Size/Year |
|--------|-----------|-----------|
| Opening | 24,000 | 12.72 GB |
| Customer | 300 | 220 MB |
| **Total** | **24,300** | **~12.94 GB** |

### 5-Year Projections

| Folder | Files (5 years) | Size (5 years) |
|--------|----------------|----------------|
| Opening | 120,000 | 63.6 GB |
| Customer | 1,500 | 1.1 GB |
| **Total** | **121,500** | **~64.7 GB** |

---

## Access Examples

### AWS CLI Commands

#### List all transactions
```bash
aws s3 ls s3://transaction-documents-demo-20251118/Opening/
```

#### View specific transaction files
```bash
aws s3 ls s3://transaction-documents-demo-20251118/Opening/TXN101557/
```

#### List customer documents
```bash
aws s3 ls s3://transaction-documents-demo-20251118/Customer/
```

#### Download specific transaction
```bash
aws s3 sync s3://transaction-documents-demo-20251118/Opening/TXN101557/ ./local/TXN101557/
```

#### Get bucket statistics
```bash
aws s3 ls s3://transaction-documents-demo-20251118/ --recursive --human-readable --summarize
```

#### Download entire bucket
```bash
aws s3 sync s3://transaction-documents-demo-20251118/ ./local-backup/
```

### S3 Console URL
```
https://s3.console.aws.amazon.com/s3/buckets/transaction-documents-demo-20251118
```

---

## File Type Distribution

### Opening Folder
```
PDF Files:  4,500 files (75%)  → 2.95 GB
XML Files:  1,500 files (25%)  → 6 MB
Total:      6,000 files        → 3.18 GB
```

### Customer Folder
```
PDF Files:  ~53 files (70%)   → ~38 MB
XML Files:  ~22 files (30%)   → ~17 MB
Total:      75 files           → 54.69 MB
```

### Overall Distribution
```
PDF Files:  4,553 files (75%)  → 2.99 GB (92%)
XML Files:  1,522 files (25%)  → 243 MB (8%)
Total:      6,075 files        → 3.23 GB
```

---

## Document Compliance

### Opening Folder Standards

Each transaction **must** contain all 4 documents:
- IDD.pdf (Identity verification)
- KYC.pdf (Regulatory compliance)
- OPA.xml (Structured agreement data)
- PID.pdf (Personal identification)

**Compliance Check:**
- Total transactions: 1,500
- Total files: 6,000
- Files per transaction: 6,000 ÷ 1,500 = **4.0 ✓**
- All transactions are compliant

### Customer Folder Standards

Variable document types based on business need:
- Mix of PDF and XML formats
- Size range: 300 KB - 1.3 MB
- Date-stamped naming for tracking

---

## Maintenance Notes

### Current Status
- Bucket created: November 18, 2025
- Data simulated for: August 20 - November 18, 2025 (3 months)
- All files uploaded successfully
- Total storage: 3.23 GB

### Regeneration
To regenerate or extend the dataset:
```bash
python3 /home/ali/s3-test/generate_s3_structure.py
```

### Backup Recommendations
- Monthly backup to Glacier for cost optimization
- Lifecycle policy for documents older than 7 years
- Versioning enabled for audit trail

---

## Summary

This S3 bucket simulates a real-world banking/financial document storage system with:
- **1,500 new account transactions** (Opening folder)
- **75 customer service documents** (Customer folder)
- **Realistic file sizes and formats**
- **3 months of historical data**
- **Scalable structure for growth**

The structure is designed to support 6,000 new accounts and 300 customer documents annually, with clear organization and compliance-ready documentation.
