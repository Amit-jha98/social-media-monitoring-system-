import os
import logging
import aiohttp
import asyncio
from dotenv import load_dotenv

load_dotenv()


class WhatsAppScraper:
    def __init__(self):
        self.api_key = os.getenv('WHATSAPP_API_KEY')
        self.base_url = 'https://graph.facebook.com/v16.0'
        if not self.api_key:
            raise ValueError("WHATSAPP_API_KEY environment variable is not set")

        logging.info("WhatsAppScraper initialized")

    async def async_search(self, keyword):
        """Asynchronously search WhatsApp for data related to a keyword."""
        try:
            logging.info("Searching WhatsApp for keyword: %s", keyword)

            url = f"{self.base_url}/whatsapp_search"
            params = {'keyword': keyword}
            headers = {'Authorization': f'Bearer {self.api_key}'}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    response_data = await response.json()

                    if response.status == 200:
                        logging.info("WhatsApp API returned data for keyword: %s", keyword)
                        return response_data.get('results', [])
                    else:
                        logging.error("WhatsApp API error: %s", response_data)
                        return None
        except Exception as e:
            logging.error("WhatsApp scraping error: %s", str(e))
            return None
