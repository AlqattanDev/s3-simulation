<#
.SYNOPSIS
    Monthly S3 Archive Script for PowerShell

.DESCRIPTION
    Archives the previous month's files from S3 into separate ZIP files:
    - One ZIP for Opening folder files
    - One ZIP for Customer folder files

    Can run as a scheduled task at the start of each month.

.PARAMETER BucketName
    S3 bucket name

.PARAMETER OutputDir
    Local directory to save ZIP files

.PARAMETER UploadToS3
    If set, upload ZIP files back to S3 in archives/ folder

.PARAMETER ReferenceDate
    Reference date for testing (default: today). Format: yyyy-MM-dd

.EXAMPLE
    .\Monthly-Archive.ps1 -BucketName "my-bucket" -OutputDir ".\archives"

.EXAMPLE
    .\Monthly-Archive.ps1 -BucketName "my-bucket" -OutputDir ".\archives" -UploadToS3

.EXAMPLE
    .\Monthly-Archive.ps1 -BucketName "my-bucket" -OutputDir ".\archives" -ReferenceDate "2025-10-15"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$BucketName,

    [Parameter(Mandatory=$true)]
    [string]$OutputDir,

    [switch]$UploadToS3,

    [string]$ReferenceDate
)

# Check if AWS CLI is available
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Error "AWS CLI is not installed or not in PATH. Please install AWS CLI first."
    exit 1
}

function Get-PreviousMonthRange {
    param([datetime]$RefDate = (Get-Date))

    # First day of current month
    $firstOfCurrentMonth = Get-Date $RefDate -Day 1 -Hour 0 -Minute 0 -Second 0 -Millisecond 0

    # Last day of previous month
    $lastOfPreviousMonth = $firstOfCurrentMonth.AddDays(-1)

    # First day of previous month
    $firstOfPreviousMonth = Get-Date $lastOfPreviousMonth -Day 1 -Hour 0 -Minute 0 -Second 0 -Millisecond 0

    # End of last day of previous month
    $endOfPreviousMonth = $firstOfCurrentMonth.AddMilliseconds(-1)

    return @{
        Start = $firstOfPreviousMonth
        End = $endOfPreviousMonth
    }
}

function Get-S3FilesInDateRange {
    param(
        [string]$Bucket,
        [string]$Prefix,
        [datetime]$StartDate,
        [datetime]$EndDate
    )

    $files = @()

    # List all objects with the prefix
    $s3Objects = aws s3api list-objects-v2 --bucket $Bucket --prefix $Prefix --query "Contents[].Key" --output json | ConvertFrom-Json

    if (-not $s3Objects) {
        return $files
    }

    foreach ($key in $s3Objects) {
        # Get object metadata
        $headOutput = aws s3api head-object --bucket $Bucket --key $key --output json 2>$null | ConvertFrom-Json

        if ($headOutput) {
            # Check for original-timestamp in metadata
            $fileDate = $null

            if ($headOutput.Metadata -and $headOutput.Metadata.'original-timestamp') {
                $timestampStr = $headOutput.Metadata.'original-timestamp'
                try {
                    $fileDate = [datetime]::ParseExact($timestampStr, 'yyyy-MM-ddTHH:mm:ss', $null)
                } catch {
                    # Fall back to LastModified
                    $fileDate = [datetime]$headOutput.LastModified
                }
            } else {
                # Use LastModified
                $fileDate = [datetime]$headOutput.LastModified
            }

            # Check if file is in our date range
            if ($fileDate -ge $StartDate -and $fileDate -le $EndDate) {
                $files += $key
            }
        }
    }

    return $files
}

function New-ZipArchive {
    param(
        [string]$Bucket,
        [array]$Files,
        [string]$ZipPath,
        [string]$TempDir
    )

    if ($Files.Count -eq 0) {
        return 0
    }

    # Create temp directory if it doesn't exist
    if (-not (Test-Path $TempDir)) {
        New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
    }

    # Download files from S3
    foreach ($fileKey in $Files) {
        $localPath = Join-Path $TempDir $fileKey
        $localDir = Split-Path $localPath -Parent

        if (-not (Test-Path $localDir)) {
            New-Item -ItemType Directory -Path $localDir -Force | Out-Null
        }

        aws s3 cp "s3://$Bucket/$fileKey" $localPath --quiet
    }

    # Create ZIP file
    Compress-Archive -Path "$TempDir\*" -DestinationPath $ZipPath -CompressionLevel Optimal -Force

    return $Files.Count
}

function Format-FileSize {
    param([long]$Bytes)

    if ($Bytes -lt 1KB) { return "$Bytes B" }
    if ($Bytes -lt 1MB) { return "{0:N2} KB" -f ($Bytes / 1KB) }
    if ($Bytes -lt 1GB) { return "{0:N2} MB" -f ($Bytes / 1MB) }
    return "{0:N2} GB" -f ($Bytes / 1GB)
}

# Main execution
try {
    # Parse reference date
    $refDate = Get-Date
    if ($ReferenceDate) {
        try {
            $refDate = [datetime]::ParseExact($ReferenceDate, 'yyyy-MM-dd', $null)
        } catch {
            Write-Error "Invalid date format: $ReferenceDate. Use yyyy-MM-dd"
            exit 1
        }
    }

    # Get date range
    $dateRange = Get-PreviousMonthRange -RefDate $refDate
    $monthStr = $dateRange.Start.ToString('yyyy-MM')

    # Create output directory
    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    }

    # Print header
    Write-Host ("=" * 70)
    Write-Host "Monthly Archive - $monthStr"
    Write-Host ("=" * 70)
    Write-Host "Date range: $($dateRange.Start.ToString('yyyy-MM-dd HH:mm:ss')) to $($dateRange.End.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Host "Source: S3 bucket: $BucketName"
    Write-Host "Output: $OutputDir"
    Write-Host ""

    $stats = @{
        Month = $monthStr
        OpeningFiles = 0
        CustomerFiles = 0
        OpeningZip = $null
        CustomerZip = $null
    }

    # Create temporary directory
    $tempDir = Join-Path $env:TEMP "s3-archive-$(Get-Random)"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

    try {
        # Process Opening folder
        Write-Host "Processing Opening folder..."
        $openingTempDir = Join-Path $tempDir "opening"
        $openingFiles = Get-S3FilesInDateRange -Bucket $BucketName -Prefix "Opening/" -StartDate $dateRange.Start -EndDate $dateRange.End
        Write-Host "  Found $($openingFiles.Count) files"

        if ($openingFiles.Count -gt 0) {
            $openingZipName = "Opening_$monthStr.zip"
            $openingZipPath = Join-Path $OutputDir $openingZipName
            $filesCount = New-ZipArchive -Bucket $BucketName -Files $openingFiles -ZipPath $openingZipPath -TempDir $openingTempDir
            $stats.OpeningFiles = $filesCount
            $stats.OpeningZip = $openingZipPath

            $zipSize = (Get-Item $openingZipPath).Length
            Write-Host "  Created: $openingZipName ($(Format-FileSize $zipSize), $filesCount files)"
        }

        # Process Customer folder
        Write-Host "`nProcessing Customer folder..."
        $customerTempDir = Join-Path $tempDir "customer"
        $customerFiles = Get-S3FilesInDateRange -Bucket $BucketName -Prefix "Customer/" -StartDate $dateRange.Start -EndDate $dateRange.End
        Write-Host "  Found $($customerFiles.Count) files"

        if ($customerFiles.Count -gt 0) {
            $customerZipName = "Customer_$monthStr.zip"
            $customerZipPath = Join-Path $OutputDir $customerZipName
            $filesCount = New-ZipArchive -Bucket $BucketName -Files $customerFiles -ZipPath $customerZipPath -TempDir $customerTempDir
            $stats.CustomerFiles = $filesCount
            $stats.CustomerZip = $customerZipPath

            $zipSize = (Get-Item $customerZipPath).Length
            Write-Host "  Created: $customerZipName ($(Format-FileSize $zipSize), $filesCount files)"
        }

        # Upload to S3 if requested
        if ($UploadToS3) {
            Write-Host "`nUploading ZIP files to S3..."
            $archivePrefix = "archives/"

            if ($stats.OpeningZip) {
                $s3Key = $archivePrefix + (Split-Path $stats.OpeningZip -Leaf)
                aws s3 cp $stats.OpeningZip "s3://$BucketName/$s3Key" --quiet
                Write-Host "  Uploaded: s3://$BucketName/$s3Key"
            }

            if ($stats.CustomerZip) {
                $s3Key = $archivePrefix + (Split-Path $stats.CustomerZip -Leaf)
                aws s3 cp $stats.CustomerZip "s3://$BucketName/$s3Key" --quiet
                Write-Host "  Uploaded: s3://$BucketName/$s3Key"
            }
        }

    } finally {
        # Clean up temp directory
        if (Test-Path $tempDir) {
            Remove-Item -Path $tempDir -Recurse -Force
        }
    }

    # Print summary
    Write-Host "`n$("=" * 70)"
    Write-Host "Archive Complete!"
    Write-Host ("=" * 70)
    Write-Host "Month: $($stats.Month)"
    Write-Host "Opening files: $($stats.OpeningFiles)"
    Write-Host "Customer files: $($stats.CustomerFiles)"
    Write-Host "Total files: $($stats.OpeningFiles + $stats.CustomerFiles)"

    if ($stats.OpeningZip) {
        Write-Host "`nOpening archive: $($stats.OpeningZip)"
    }
    if ($stats.CustomerZip) {
        Write-Host "Customer archive: $($stats.CustomerZip)"
    }

    exit 0

} catch {
    Write-Error "Error: $_"
    exit 1
}
