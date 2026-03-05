"""
Instagram Scraper Module (Deprecated)

This module previously contained an unofficial Instagram scraper using Instaloader.
It has been removed due to security concerns:
  - Hardcoded credentials were embedded in the source code
  - Unofficial scraping violates Instagram's Terms of Service

For Instagram data collection, use the official Instagram Graph API via:
    api/scraping/instagram_api_scraper.py

Configure the following environment variables in .env:
    INSTAGRAM_ACCESS_TOKEN=your_access_token
    INSTAGRAM_USER_ID=your_user_id
"""
