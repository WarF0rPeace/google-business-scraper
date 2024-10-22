import httpx
import re
from modules.logger import get_logger
from urllib.parse import urlparse
logger = get_logger(__name__)

def create_client():
    return httpx.AsyncClient()

async def fetch_url(client, url, feature_id):
    domain_pattern = re.compile(
        r'^(https?://)?(www\.)?(instagram\.com|instagr\.am|instagr\.com|facebook\.com|fb\.com|fb\.me|youtube\.com|youtu\.be|linkedin\.com|twitter\.com|x\.com|tiktok\.com)(/.*)?$'
    )
    if domain_pattern.match(url): return url, feature_id
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }
    try:
        response = await client.get(url, headers=headers, follow_redirects=True, timeout=3)
        response.raise_for_status()
        return response.text, feature_id
    except httpx._exceptions.HTTPStatusError as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return None, feature_id
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching {url}: {e}")
        return None, feature_id

class EmailExtractor:
    @staticmethod
    def extract(text):
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        mails = re.findall(email_pattern, text)
        return list(set(mails))

class InstagramExtractor:
    @staticmethod
    def extract(text):
        instagram_pattern = instagram_pattern = r'(?:(?:http|https):\/\/)?(?:www\.)?(?:instagram\.com|instagr\.am|instagr\.com)\/(?!p\/|direct\/|accounts\/|call\/|explore\/|stories\/|reels\/|about\/|help\/|privacy\/|terms\/|admin\/|oauth\/|p$|direct$|accounts$|call$|explore$|stories$|reels$|about$|help$|privacy$|terms$|admin$|oauth$)([\w\.]{1,30})(?:\/[^\s]*)?'
        usernames = re.findall(instagram_pattern, text)
        return list(set(f"https://instagram.com/{username}" for username in usernames))

class FacebookExtractor:
    @staticmethod
    def extract(text):
        facebook_pattern = r'(?:https?:\/\/)?(?:www\.)?(?:mbasic\.facebook|m\.facebook|facebook|fb)\.(?:com|me)\/(?!sharer\/)(?:(?:\w\.)*#!\/)?(?:pages\/)?(?:[\w\-\.]*\/)*(?:profile\.php\?id=\d+|[\w\-]+)(?:[\/#][^\s!"\'<>?@#$%^&*()]+)?'
        links = re.findall(facebook_pattern, text)
        return list(set(links))

class YoutubeExtractor:
    @staticmethod
    def extract(text):
        youtube_pattern = r'https?:\/\/(?:www\.)?(?:youtube(?:-nocookie)?\.com\/(?:channel\/[\w-]+|c\/[\w-]+|user\/[\w-]+|@[\w-]+))'
        links = re.findall(youtube_pattern, text)
        return list(set(links))

class LinkedinExtractor:
    @staticmethod
    def extract(text):
        linkedin_pattern = r'(?:https?:\/\/)?(?:www\.)?(?:linkedin\.com\/(?:in|pub)\/[\w-]+)'
        links = re.findall(linkedin_pattern, text)
        return list(set(links))
    
class TwitterExtractor:
    @staticmethod
    def extract(text):
        twitter_pattern = r'(?:https?:\/\/)?(?:www\.)?(?:twitter\.com|x\.com)\/(?:@?[\w-]+)(?=[\/]?|$)'
        links = re.findall(twitter_pattern, text)
        return list(set(links))
    
class TiktokExtractor:
    @staticmethod
    def extract(text):
        tiktok_pattern = r'(?:https?:\/\/)?(?:www\.)?tiktok\.com\/@?[\w.-]+'
        links = re.findall(tiktok_pattern, text)
        return list(set(links))
    