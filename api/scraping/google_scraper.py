import sys
import asyncio
import aiohttp
import logging
from pathlib import Path
from datetime import datetime, timezone
import os
from typing import List, Dict
from dotenv import load_dotenv
load_dotenv()
# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GoogleScraper:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.cse_id = os.getenv('GOOGLE_CSE_ID')
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        if not self.api_key or not self.cse_id:
            logger.error("Google API credentials are not set properly.")
            raise ValueError("Missing Google API credentials.")

    async def async_search_keyword(self, keyword: str) -> List[Dict]:
        """Asynchronously perform a Google Custom Search for the given keyword using aiohttp."""
        return await self._search(keyword)

    async def async_search(self, keyword: str) -> List[Dict]:
        """Alias for async_search_keyword for compatibility with ScraperManager."""
        return await self._search(keyword)

    async def _search(self, keyword: str) -> List[Dict]:
        """Internal search implementation."""
        params = {
            "key": self.api_key,
            "cx": self.cse_id,
            "q": keyword
        }
        try:
            logger.info(f"Starting Google search for keyword: {keyword}")
            
            # Using aiohttp for non-blocking HTTP request
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    response.raise_for_status()
                    results = await response.json()
                    logger.info(f"Google search completed for keyword: {keyword}")
                    
                    timestamp = datetime.now(timezone.utc)  # Get the current UTC time
                    
                    # Process and return results with content, link, and image/profile link
                    processed_results = []
                    for item in results.get("items", []):
                        processed_result = {
                            "content": item.get("snippet", ""),
                            "link": item.get("link", ""),
                            "timestamp": timestamp
                        }
                        # Attempt to fetch an image or profile link if available
                        pagemap = item.get("pagemap", {})
                        if pagemap:
                            # Get the first image link if available
                            cse_image = pagemap.get("cse_image", [{}])[0].get("src", "")
                            if cse_image:
                                processed_result["image_link"] = cse_image
                            # Get a profile or related link if available
                            cse_thumbnail = pagemap.get("cse_thumbnail", [{}])[0].get("src", "")
                            if cse_thumbnail:
                                processed_result["profile_link"] = cse_thumbnail
                        
                        processed_results.append(processed_result)
                    return processed_results
        except aiohttp.ClientError as e:
            logger.error(f"Google scraping error for keyword '{keyword}': {str(e)}")
            return []

if __name__ == "__main__":
    # For testing purposes
    scraper = GoogleScraper()
    keywords = ["example keyword", "test search"]  # Example keywords for testing

    async def run_test():
        for keyword in keywords:
            results = await scraper.async_search_keyword(keyword)
            print(f"Found {len(results)} results for '{keyword}'")
            for result in results:
                print(f"Content: {result['content']}, Link: {result.get('link')}, "
                      f"Image Link: {result.get('image_link')}, "
                      f"Profile Link: {result.get('profile_link')}, "
                      f"Timestamp: {result['timestamp']}")

    asyncio.run(run_test())
