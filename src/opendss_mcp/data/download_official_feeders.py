#!/usr/bin/env python3
"""
Download official IEEE test feeders from EPRI's OpenDSS repository.

This script downloads the official IEEE 13, 34, and 123 bus test feeders
from the OpenDSS SourceForge repository and saves them to the local
data directory.

Usage:
    python download_official_feeders.py
"""

import sys
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple


# URLs for official IEEE test feeders and their dependencies from OpenDSS repository
FEEDER_URLS: Dict[str, str] = {
    "IEEELineCodes.dss": "https://sourceforge.net/p/electricdss/code/HEAD/tree/trunk/Distrib/IEEETestCases/IEEELineCodes.dss?format=raw",
    "IEEE13.dss": "https://sourceforge.net/p/electricdss/code/HEAD/tree/trunk/Distrib/IEEETestCases/13Bus/IEEE13Nodeckt.dss?format=raw",
    "IEEE34.dss": "https://sourceforge.net/p/electricdss/code/HEAD/tree/trunk/Distrib/IEEETestCases/34Bus/ieee34Mod1.dss?format=raw",
    "IEEE123.dss": "https://sourceforge.net/p/electricdss/code/HEAD/tree/trunk/Distrib/IEEETestCases/123Bus/IEEE123Master.dss?format=raw",
}

# Target directory for downloaded feeders
FEEDERS_DIR = Path(__file__).parent / "ieee_feeders"


def download_file(url: str, destination: Path) -> bool:
    """Download a file from a URL to a local destination.

    Args:
        url: URL of the file to download
        destination: Local path where the file should be saved

    Returns:
        bool: True if download was successful, False otherwise
    """
    try:
        print(f"  Downloading from: {url}")
        print(f"  Saving to: {destination}")

        # Download the file
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read()

        # Write to destination
        with open(destination, "wb") as f:
            f.write(content)

        # Verify the file was written
        if destination.exists() and destination.stat().st_size > 0:
            file_size = destination.stat().st_size
            print(f"  ✅ Downloaded successfully ({file_size} bytes)")
            return True
        else:
            print(f"  ❌ File was not created or is empty")
            return False

    except urllib.error.URLError as e:
        print(f"  ❌ Network error: {e.reason}")
        return False
    except urllib.error.HTTPError as e:
        print(f"  ❌ HTTP error {e.code}: {e.reason}")
        return False
    except OSError as e:
        print(f"  ❌ File system error: {str(e)}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {str(e)}")
        return False


def download_all_feeders() -> Tuple[int, int]:
    """Download all IEEE test feeders.

    Returns:
        Tuple of (successful_count, failed_count)
    """
    # Ensure target directory exists
    FEEDERS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Target directory: {FEEDERS_DIR}\n")

    successful = 0
    failed = 0
    failed_feeders: List[str] = []

    for filename, url in FEEDER_URLS.items():
        print(
            f"[{successful + failed + 1}/{len(FEEDER_URLS)}] Downloading {filename}..."
        )

        # Determine destination filename
        destination = FEEDERS_DIR / filename

        # Download the file
        if download_file(url, destination):
            successful += 1
        else:
            failed += 1
            failed_feeders.append(filename)

        print()  # Empty line for readability

    # Print summary
    print("=" * 80)
    print("DOWNLOAD SUMMARY")
    print("=" * 80)
    print(f"✅ Successful: {successful}/{len(FEEDER_URLS)}")

    if failed > 0:
        print(f"❌ Failed: {failed}/{len(FEEDER_URLS)}")
        print(f"   Failed feeders: {', '.join(failed_feeders)}")

    return successful, failed


def main() -> int:
    """Main entry point for the download script.

    Returns:
        Exit code (0 for success, 1 for partial failure, 2 for complete failure)
    """
    print("=" * 80)
    print("OpenDSS IEEE Test Feeder Downloader")
    print("=" * 80)
    print("This script downloads official IEEE test feeders from EPRI's repository\n")

    try:
        successful, failed = download_all_feeders()

        if failed == 0:
            print("\n🎉 All feeders downloaded successfully!")
            return 0
        elif successful > 0:
            print("\n⚠️  Some feeders failed to download. Check errors above.")
            return 1
        else:
            print("\n❌ All downloads failed. Check your internet connection.")
            return 2

    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
