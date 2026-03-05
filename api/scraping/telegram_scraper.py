# import os
# import time
# import logging
# import asyncio
# from telethon import TelegramClient, errors
# from threading import Lock, Thread
# import random
# from dotenv import load_dotenv
# from telethon.errors import RPCError, FloodWaitError
# from sqlite3 import OperationalError

# load_dotenv()

# # Initialize logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# # Global file lock to prevent simultaneous access
# file_lock = Lock()

# class TelegramScraper:
#     def __init__(self):
#         self.api_id = os.getenv('TELEGRAM_API_ID')
#         self.api_hash = os.getenv('TELEGRAM_API_HASH')
#         self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

#         if not self.api_id or not self.api_hash:
#             raise ValueError("API ID or API Hash is not set in the environment variables")

#         # Create a unique session file using process ID and timestamp
#         self.session_file = f'telegram_user_session_{os.getpid()}_{int(time.time())}.session'
#         self.client = None
#         self.searched_keywords = set()

#     async def initialize_client(self, retries=5, delay=10):
#         """Initialize the Telegram client using a bot token or user account asynchronously."""
#         attempt = 0
#         while attempt < retries:
#             try:
#                 with file_lock:
#                     if self.bot_token:
#                         logger.info("Initializing Telegram client with bot token")
#                         temp_client = TelegramClient(self.session_file, api_id=self.api_id, api_hash=self.api_hash)
#                         await temp_client.start(bot_token=self.bot_token)
#                         self.client = temp_client
#                     else:
#                         logger.info("Initializing Telegram client with user account")
#                         temp_client = TelegramClient(
#                             self.session_file,
#                             api_id=self.api_id,
#                             api_hash=self.api_hash
#                         )
#                         await temp_client.start()
#                         self.client = temp_client

#                     if await self.client.is_user_authorized():
#                         logger.info("Telegram client successfully connected and authorized.")
#                         return
#             except OperationalError as e:
#                 attempt += 1
#                 logger.error(f"Database lock error during initialization: {e}. Attempt {attempt}/{retries}")
#                 await asyncio.sleep(delay)
#             except PermissionError as e:
#                 logger.error(f"Permission error during initialization: {e}")
#                 await self.retry_file_cleanup()
#             except Exception as e:
#                 logger.error(f"Error initializing Telegram client: {e}")
#                 await self.retry_file_cleanup()

#         logger.error("Failed to initialize Telegram client after multiple retries.")
#         self.client = None

#     async def retry_file_cleanup(self, retries=3, delay=5):
#         """Retry cleanup of session file in case of access conflicts."""
#         for attempt in range(retries):
#             try:
#                 if os.path.exists(self.session_file):
#                     os.remove(self.session_file)
#                     logger.info("Session file cleaned up successfully.")
#                 break
#             except PermissionError:
#                 if attempt < retries - 1:
#                     logger.info("Retrying file cleanup after delay...")
#                     await asyncio.sleep(delay)
#                 else:
#                     logger.error("Failed to clean up session file after multiple retries.")
#             except Exception as e:
#                 logger.error(f"Unexpected error during file cleanup: {e}")

#     async def async_search(self, keyword):
#         """Perform asynchronous search globally for a specific keyword on Telegram."""
#         logger.info(f"Starting async search for keyword: {keyword}")

#         # Check if client is initialized and connected
#         if self.client is None or not await self.client.is_user_authorized():
#             logger.info("Client is not initialized or disconnected, attempting to reconnect.")
#             await self.initialize_client()

#         if self.client is None:
#             logger.error(f"Failed to initialize client for keyword '{keyword}'.")
#             return []

#         result = []
#         try:
#             async for message in self.client.iter_messages(keyword, limit=100):
#                 if message.text:
#                     logger.debug(f"Message found: {message.text}")
#                     result.append({
#                         'content': message.text,
#                         'timestamp': message.date,
#                         'chat_id': message.chat_id,
#                         'sender_id': message.sender_id
#                     })

#             if result:
#                 logger.info(f"Found {len(result)} messages for keyword: {keyword}")
#             else:
#                 logger.info(f"No messages found for keyword: {keyword}")

#             return result

#         except FloodWaitError as e:
#             wait_time = e.seconds + random.randint(5, 15)
#             logger.warning(f"FloodWaitError for keyword '{keyword}': Retrying after {wait_time} seconds.")
#             await asyncio.sleep(wait_time)
#             return await self.async_search(keyword)
#         except RPCError as e:
#             logger.error(f"RPC error while searching for keyword '{keyword}': {e}")
#             await self.initialize_client()
#             return []
#         except Exception as e:
#             logger.error(f"Error while searching for keyword '{keyword}': {e}")
#             return []

#     async def search_keywords(self, keywords):
#         """Search through a list of keywords asynchronously."""
#         try:
#             for keyword in keywords:
#                 if keyword in self.searched_keywords:
#                     logger.info(f"Keyword '{keyword}' already processed, skipping.")
#                     continue

#                 self.searched_keywords.add(keyword)
#                 result = await self.async_search(keyword)

#                 if result:
#                     logger.info(f"Storing {len(result)} results for keyword '{keyword}'.")
#                 else:
#                     logger.warning(f"No results to store for keyword '{keyword}'.")
#         except Exception as e:
#             logger.error(f"Error in search_keywords method: {e}")

# async def run(keywords):
#     """Entry point for running the Telegram scraper asynchronously."""
#     try:
#         logger.info("Starting Telegram scraping process.")
#         scraper = TelegramScraper()
#         await scraper.initialize_client()
#         await scraper.search_keywords(keywords)
#         logger.info("Telegram scraping process completed.")
#     except Exception as e:
#         logger.error(f"Error in run method: {e}")

# def start_scraper_in_thread(keywords):
#     """Starts the Telegram scraper in a separate thread with its own event loop."""
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.run_until_complete(run(keywords))

# # If run as a script
# if __name__ == "__main__":
#     keywords_to_search = ["puria", "maal", "example"]
#     scraper_thread = Thread(target=start_scraper_in_thread, args=(keywords_to_search,))
#     scraper_thread.start()
#     scraper_thread.join()
