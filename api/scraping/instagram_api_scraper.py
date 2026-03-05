import os
import logging
import asyncio
import requests
from dotenv import load_dotenv

load_dotenv()


class InstagramScraper:
    def __init__(self, access_token=None):
        self.access_token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.base_url = "https://graph.facebook.com/v16.0"
        self.instagram_user_id = os.getenv("INSTAGRAM_USER_ID")

        if not self.access_token or not self.instagram_user_id:
            raise ValueError("Environment variables INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID must be set")

        logging.info("InstagramScraper initialized")

    def search_hashtag_id(self, keyword):
        """Fetch the hashtag ID for a given keyword."""
        try:
            logging.info("Searching for hashtag ID for keyword: %s", keyword)
            url = f"{self.base_url}/ig_hashtag_search"
            params = {
                "user_id": self.instagram_user_id,
                "q": keyword,
                "access_token": self.access_token,
            }
            response = requests.get(url, params=params)
            response_data = response.json()

            if response.status_code == 200:
                hashtag_id = response_data.get("data", [{}])[0].get("id")
                logging.info("Hashtag ID for '%s': %s", keyword, hashtag_id)
                return hashtag_id
            else:
                logging.error("Error fetching hashtag ID: %s", response_data)
                return None
        except Exception as e:
            logging.error("Error during hashtag ID search: %s", str(e))
            return None

    def fetch_posts_by_hashtag(self, hashtag_id):
        """Fetch posts associated with a hashtag ID."""
        try:
            logging.info("Fetching posts for hashtag ID: %s", hashtag_id)
            url = f"{self.base_url}/{hashtag_id}/recent_media"
            params = {
                "user_id": self.instagram_user_id,
                "fields": "id,caption,media_type,media_url,permalink,timestamp,comments_count,like_count",
                "access_token": self.access_token,
            }
            response = requests.get(url, params=params)
            response_data = response.json()

            if response.status_code == 200:
                logging.info("Successfully fetched posts for hashtag ID: %s", hashtag_id)
                return response_data.get("data", [])
            else:
                logging.error("Error fetching posts: %s", response_data)
                return None
        except Exception as e:
            logging.error("Error during fetch posts by hashtag: %s", str(e))
            return None

    def search_public_data(self, keyword):
        """Search public posts and accounts based on a keyword."""
        hashtag_id = self.search_hashtag_id(keyword)
        if not hashtag_id:
            logging.warning("No hashtag ID found for keyword: %s", keyword)
            return None

        posts = self.fetch_posts_by_hashtag(hashtag_id)
        if not posts:
            logging.warning("No posts found for hashtag ID: %s", hashtag_id)
        return posts

    async def async_search(self, keyword):
        """Async wrapper for search_public_data - compatible with ScraperManager."""
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, self.search_public_data, keyword)
            if results:
                return [post.get("caption", "") for post in results if post.get("caption")]
            return []
        except Exception as e:
            logging.error("Error during async Instagram search: %s", str(e))
            return []

    def fetch_user_media(self):
        """Fetch all media from the user's account."""
        try:
            logging.info("Fetching user media...")
            url = "https://graph.instagram.com/me/media"
            params = {
                "fields": "id,caption,media_type,media_url,timestamp",
                "access_token": self.access_token
            }
            response = requests.get(url, params=params)
            response_data = response.json()

            if response.status_code == 200:
                media_data = response_data.get("data", [])
                logging.info("Successfully fetched user media")
                return media_data
            else:
                logging.error("Error fetching user media: %s", response_data)
                return None
        except Exception as e:
            logging.error("Error during fetch_user_media: %s", str(e))
            return None

    def fetch_post_details(self, post_id):
        """Fetch details of a specific post, including comments and tags."""
        try:
            logging.info("Fetching details for post ID: %s", post_id)
            url = f"https://graph.instagram.com/{post_id}"
            params = {
                "fields": "id,caption,media_type,media_url,timestamp,comments{username,text}",
                "access_token": self.access_token
            }
            response = requests.get(url, params=params)
            response_data = response.json()

            if response.status_code == 200:
                logging.info("Successfully fetched post details")
                return response_data
            else:
                logging.error("Error fetching post details: %s", response_data)
                return None
        except Exception as e:
            logging.error("Error during fetch_post_details: %s", str(e))
            return None

    def search_keyword_in_posts(self, keyword):
        """Search for a keyword in captions and comments of all user media."""
        try:
            logging.info("Searching for keyword '%s' in user media...", keyword)
            media = self.fetch_user_media()
            if not media:
                logging.warning("No media available for search")
                return None

            matching_posts = [
                post for post in media
                if self._post_matches_keyword(post, keyword)
            ]

            if matching_posts:
                logging.info("Found %d posts matching the keyword '%s'", len(matching_posts), keyword)
                return matching_posts

            logging.warning("No posts found for keyword '%s'", keyword)
            return None
        except Exception as e:
            logging.error("Error during search_keyword_in_posts: %s", str(e))
            return None

    def _post_matches_keyword(self, post, keyword):
        """Check if a post's caption or comments contain the keyword."""
        keyword_lower = keyword.lower()
        if keyword_lower in post.get("caption", "").lower():
            return True

        post_details = self.fetch_post_details(post["id"])
        if not post_details or "comments" not in post_details:
            return False

        return any(
            keyword_lower in comment["text"].lower()
            for comment in post_details["comments"]["data"]
        )


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = InstagramScraper()

    keyword = "nature"
    logging.info("Searching for public posts using keyword: '%s'", keyword)
    posts = scraper.search_public_data(keyword)

    if posts:
        for post in posts:
            logging.info("Post ID: %s | Caption: %s | URL: %s", post["id"], post.get("caption", ""), post.get("permalink", ""))
    else:
        logging.warning("No public posts found for the keyword: '%s'", keyword)
