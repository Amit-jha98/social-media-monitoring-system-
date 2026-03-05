import asyncio
import os
import logging
from datetime import datetime
from threading import Thread
from importlib import import_module
from database.db_queries import fetch_keyword_batch, store_raw_data
from utils.encryption_utils import EncryptionUtils

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class ScraperManager:
    def __init__(self, batch_size=100, use_official=True):
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            raise ValueError("ENCRYPTION_KEY environment variable is not set")

        self.encryption_utils = EncryptionUtils(encryption_key)
        self.batch_size = batch_size
        self.results = {"scrapedData": [], "errors": [], "notifications": []}
        self.use_official = use_official
        self.platform_scrapers = self._load_scrapers()

        logging.info("ScraperManager initialized with batch size: %s", self.batch_size)

    def _load_scrapers(self):
        """Dynamically load scrapers for each platform."""
        scrapers = {}
        scraper_configs = {
            "Google": ("api.scraping.google_scraper", "GoogleScraper"),
            "Telegram": ("api.scraping.telegram_scraper", "TelegramScraper"),
            "Instagram": ("api.scraping.instagram_api_scraper" if self.use_official else "api.scraping.instagram_scraper", "InstagramScraper"),
            "WhatsApp": ("api.scraping.whatsapp_api_scraper" if self.use_official else "api.scraping.whatsapp_scraper", "WhatsAppScraper"),
        }

        for platform, (module_path, class_name) in scraper_configs.items():
            try:
                module = import_module(module_path)
                scraper_class = getattr(module, class_name)
                scrapers[platform] = scraper_class()
                logging.info("%s scraper loaded successfully.", platform)
            except ImportError as e:
                logging.error("Failed to load %s scraper: %s", platform, str(e))
            except AttributeError as e:
                logging.error("%s scraper class not found in module: %s", platform, str(e))

        return scrapers

    def scrape_all_platforms(self):
        """Start the scraping process for all platforms asynchronously."""
        try:
            logging.info("Starting scraping process for all platforms.")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._scrape())
        except Exception as e:
            logging.error("Scraping error: %s", str(e))
            self.results["errors"].append(f"Scraping error: {str(e)}")
        finally:
            logging.info("Scraping process completed.")

    async def _scrape(self):
        """Fetch keywords and scrape across all platforms."""
        while True:
            logging.info("Fetching keyword batch of size: %s", self.batch_size)
            keywords = fetch_keyword_batch(self.batch_size)

            if not keywords:
                logging.info("No keywords left to scrape.")
                self.results["notifications"].append("No keywords left to scrape.")
                break

            tasks = [self.scrape_platforms(keyword['keyword']) for keyword in keywords]
            await asyncio.gather(*tasks)

    async def scrape_platforms(self, keyword_text):
        """Asynchronously scrape data for the given keyword across all platforms."""
        tasks = []
        for platform, scraper in self.platform_scrapers.items():
            # Support both async_search and async_search_keyword method names
            search_method = None
            if hasattr(scraper, "async_search"):
                search_method = scraper.async_search
            elif hasattr(scraper, "async_search_keyword"):
                search_method = scraper.async_search_keyword

            if search_method:
                try:
                    tasks.append(
                        asyncio.create_task(self.scrape_platform(keyword_text, search_method, platform))
                    )
                except Exception as e:
                    logging.error("Failed to start scraping for %s: %s", platform, str(e))
                    self.results["errors"].append(f"Error triggering {platform}: {str(e)}")

        logging.info("Waiting for all scraping tasks for keyword '%s' to complete.", keyword_text)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            platform = list(self.platform_scrapers.keys())[i]
            if isinstance(result, Exception):
                logging.error("%s scraping failed for keyword '%s': %s", platform, keyword_text, str(result))
                self.results["errors"].append(f"{platform} scraping error: {str(result)}")
            else:
                logging.info("%s scraping completed successfully for keyword '%s'.", platform, keyword_text)

    async def scrape_platform(self, keyword_text, scraper_method, platform):
        """Scrape a specific platform for the given keyword."""
        try:
            logging.info("Starting %s scraping for keyword: %s", platform, keyword_text)
            platform_data = await scraper_method(keyword_text)

            if platform_data:
                logging.info("Data scraped from %s for keyword '%s'. Data size: %d", platform, keyword_text, len(platform_data))
                self.store_data(keyword_text, platform, platform_data)
                self.results["scrapedData"].append({platform: platform_data})
            else:
               
                logging.warning("No data found on %s for keyword '%s'.", platform, keyword_text)
                self.results["notifications"].append(f"No data found on {platform} for keyword: {keyword_text}")
        except Exception as e:
            logging.error("Error during %s scraping for keyword '%s': %s", platform, keyword_text, str(e))
            self.results["errors"].append(f"{platform} scraping error: {str(e)}")

    def store_data(self, keyword_text, platform, data):
        """Store the scraped data in the database."""
        try:
            logging.info("Storing data for keyword '%s' from platform '%s'.", keyword_text, platform)
            encrypted_data = [self.encryption_utils.encrypt(item) for item in data]
            store_raw_data(keyword=keyword_text, platform=platform, encrypted_content=encrypted_data)
            logging.info("Data successfully stored for keyword '%s' from platform '%s'.", keyword_text, platform)
        except Exception as e:
            logging.error("Failed to store data for keyword '%s' from platform '%s': %s", keyword_text, platform, str(e))
            self.results["errors"].append(f"Storage error for {platform}, keyword: {keyword_text} - {str(e)}")

    def start_scraping_thread(self):
        """Start scraping in a separate thread to prevent blocking."""
        logging.info("Starting scraping in a separate thread.")
        thread = Thread(target=self.scrape_all_platforms, daemon=True)
        thread.start()
        logging.info("Scraping thread started successfully.")


if __name__ == "__main__":
    # Initialize ScraperManager and begin scraping
    try:
        scraper_manager = ScraperManager(batch_size=100, use_official=True)
        scraper_manager.start_scraping_thread()
    except Exception as e:
        logging.critical("Critical error initializing ScraperManager: %s", str(e))
