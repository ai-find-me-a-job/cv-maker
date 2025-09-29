#!/usr/bin/env python3
"""
Setup script for Playwright browsers.
Run this after installing the playwright package.
"""

import subprocess
import sys


def install_playwright_browsers():
    """Install Playwright browsers."""
    print("Installing Playwright browsers...")
    print("This may take a few minutes...")
    
    try:
        # Install Playwright browsers
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install", "chromium"
        ], capture_output=True, text=True, check=True)
        
        print("✓ Chromium browser installed successfully")
        print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install browsers: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("✗ Playwright not found. Please install it first:")
        print("   pip install playwright")
        return False


def main():
    print("Playwright Browser Setup")
    print("========================")
    
    success = install_playwright_browsers()
    
    if success:
        print("\n✓ Setup complete! You can now use the web scraper.")
        print("\nTo test the scraper:")
        print("   python test_web_scraper.py")
    else:
        print("\n✗ Setup failed. Please check the error messages above.")
        print("\nManual installation:")
        print("1. pip install playwright")
        print("2. playwright install chromium")


if __name__ == "__main__":
    main()