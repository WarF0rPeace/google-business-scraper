import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup as bs
import httpx
import asyncio
from urllib.parse import unquote
from PySide6.QtCore import QThread, Signal
from modules.logger import get_logger

logger = get_logger(__name__)

class GoogleEarthClient:
    BASE_URL = "https://www.google.com/earth/rpc/search"
    FEATURE_BASE_URL = "https://www.google.com/earth/rpc/entity"

    def __init__(self, query, session, start=0):
        self.query = query
        self.start = start
        self.session = session
        self.headers = {
            "User-Agent": "GoogleEarth/7.3.6.9796(Windows;Microsoft Windows (6.2.9200.0);tr;kml:2.2;client:Pro;type:default)",
            "Accept-Encoding": "deflate, br",
            "Accept-Language": "tr-TR,en,*"
        }

    async def fetch_data(self, url, params):
        try:
            response = await self.session.get(url, headers=self.headers, params=params, timeout=5)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Error fetching data from {url}: {e}", exc_info=True)
            return None

    async def fetch_category(self, feature_id):
        if feature_id is None:
            return None
        params = {
            "lat": 0,
            "lng": 0,
            "fid": feature_id,
            "hl": "tr",
            "gl": "tr",
            "client": "earth-client",
            "cv": "7.3.6.9796"
        }
        return await self.fetch_data(self.FEATURE_BASE_URL, params)

    async def get_places(self):
        xml_data = await self.fetch_data(self.BASE_URL, {
            "q": self.query,
            "start": self.start,
            "hl": "en",
            "gl": "en",
            "client": "earth-client",
            "cv": "7.3.6.9796",
            "useragent": self.headers['User-Agent'],
            "output": "xml"
        })
        return self.parse_xml(xml_data)

    def parse_category_html(self, html_data):
        if html_data is None:
            return None
        soup = bs(html_data, 'html.parser')
        category = soup.find("span", class_="Qfo35d")
        return category.text if category else None

    def parse_xml(self, xml_data):
        if xml_data is None:
            logger.warning("No XML data to parse.")
            return [], False
        
        try:
            root = ET.fromstring(xml_data)
            places = []
            more_places = root.find(".//omnibox_content").get('more_place_cards_available') == 'true'

            for place_card in root.findall(".//place_card"):
                title = place_card.find("title").text
                address_lines = place_card.findall("address_line")
                address = " ".join(line.text for line in address_lines if line.text) or None
                phone_number = place_card.find("phone_number").text if place_card.find("phone_number") is not None else None
                feature_id = place_card.find("feature_id").text if place_card.find("feature_id") is not None else None
                authority_page_link = place_card.find("authority_page_link")
                url = authority_page_link.find("url").text if authority_page_link is not None else None
                
                if url:
                    url = unquote(url.split("/url?q=")[-1].split("&opi=")[0])

                rating = place_card.find("rating")
                rating_score = rating.get("num_rating_stars") if rating else None
                review_count_element = rating.find(".//review_count/anchor_text") if rating is not None else None
                review_count = review_count_element.text.split()[0] if review_count_element is not None else 0
                
                rating_score = float(rating_score) if rating_score else 0
                review_count = int(review_count)

                places.append({
                    "title": title,
                    "address": address,
                    "phone_number": phone_number,
                    "feature_id": feature_id,
                    "url": url,
                    "rating_score": rating_score,
                    "review_count": review_count
                })
            logger.info(f"Successfully parsed {len(places)} places.")
            return places, more_places
        except Exception as e:
            logger.error(f"Error parsing XML data: {e}", exc_info=True)
            return [], False


class ScraperWorker(QThread):
    update_data = Signal(dict)
    finished = Signal()

    def __init__(self, queries, max_concurrent_requests=5):
        super().__init__()
        self.queries = queries
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)

    def run(self):
        logger.info("Starting scraper worker thread.")
        asyncio.run(self.scrape())
        self.finished.emit()
        logger.info("Scraper worker thread finished.")

    async def scrape(self):
        async with httpx.AsyncClient() as session:
            seen_feature_ids = set()

            async def fetch_places(query):
                client = GoogleEarthClient(query, session)
                more_places = True
                start = 0

                while more_places:
                    async with self.semaphore:
                        client.start = start
                        places, more_places = await client.get_places()
                        start += len(places)

                        category_tasks = []
                        unique_places = []

                        for place in places:
                            feature_id = place.get("feature_id")
                            if feature_id:
                                feature_id = feature_id.strip().lower()

                            if feature_id and feature_id not in seen_feature_ids:
                                seen_feature_ids.add(feature_id)
                                category_tasks.append(client.fetch_category(feature_id))
                                unique_places.append(place)

                        categories = await asyncio.gather(*category_tasks)
                        for place, category_html in zip(unique_places, categories):
                            category = client.parse_category_html(category_html)
                            place['category'] = category
                            self.update_data.emit(place)
                            # logger.info(f"Updated place with feature_id: {place['feature_id']} and category: {category}")

            tasks = [fetch_places(query) for query in self.queries]
            await asyncio.gather(*tasks)
