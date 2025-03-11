import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup as bs
import asyncio
from urllib.parse import unquote
from PySide6.QtCore import QThread, Signal
from utils import fetch_utils
from utils.constants import CHECKBOX_OPTIONS
from modules.logger import get_logger
import re

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
    
    def parse_lat_long_html(self, html_data):
        if html_data is None:
            return None
        soup = bs(html_data, 'html.parser')
        map_div = soup.find('div', class_='jK1Lre')
        if not map_div:
            return None
        map_link = map_div.find('a', href=True, text=re.compile('Google Haritalar'))
        if not map_link:
            return None
        url = map_link['href']
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if match:
            latitude, longitude = match.groups()
            return float(latitude), float(longitude)
        return None

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
                review_count_element = rating.find(".//review_count/anchor_text") if rating else None
                review_count_element = rating.find(".//review_count/anchor_text") if rating else None
                review_count_text = review_count_element.text.split()[0] if review_count_element is not None else '0'

                try:
                    review_count = int(review_count_text.replace(',', '').strip())
                except ValueError:
                    review_count = 0

                rating_score = float(rating_score) if rating_score else 0
                
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

    def __init__(self, queries, options={}, max_concurrent_requests=5):
        super().__init__()
        self.queries = queries
        self.options = options
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self._stop_event = asyncio.Event()
        self.session = fetch_utils.create_client()
        self.client = None

    def run(self):
        logger.info("Starting scraper worker thread.")
        asyncio.run(self.scrape())
        self.finished.emit()
        logger.info("Scraper worker thread finished.")

    async def scrape(self):
        self.client = GoogleEarthClient("", self.session)
        seen_feature_ids = set()

        async def fetch_places(query):
            self.client.query = query
            more_places = True
            start = 0

            while more_places:
                if self._stop_event.is_set():
                    logger.info("Scraping stopped by user.")
                    return

                async with self.semaphore:
                    self.client.start = start
                    places, more_places = await self.client.get_places()
                    start += len(places)
                    unique_places = [place for place in places if place.get("feature_id") not in seen_feature_ids]

                    for place in unique_places:
                        seen_feature_ids.add(place.get("feature_id"))

                    parse_category = self.options.get("category", False)
                    parse_lat_long = self.options.get("lat_long", False)

                    if parse_category or parse_lat_long:
                        tasks = [self.client.fetch_category(place.get("feature_id")) for place in unique_places]
                        results = await asyncio.gather(*tasks)

                        for place, result in zip(unique_places, results):
                            if isinstance(result, str):
                                if parse_category:
                                    category = self.client.parse_category_html(result)
                                    place['category'] = category
                                if parse_lat_long:
                                    lat_long = self.client.parse_lat_long_html(result)
                                    place['lat_long'] = lat_long

                    if any(self.options.get(option, False) for option in CHECKBOX_OPTIONS if CHECKBOX_OPTIONS[option].get("req", False)):

                        url_tasks = [
                            fetch_utils.fetch_url(self.session, place.get("url"), place.get("feature_id")) 
                            for place in unique_places if place.get("url")
                        ]
                        page_contents = await asyncio.gather(*url_tasks)

                        for (page_content, feature_id), place in zip(page_contents, unique_places):
                            if page_content:
                                matched_place = next((p for p in unique_places if p.get("feature_id") == feature_id), None)
                                if matched_place:
                                    for option in CHECKBOX_OPTIONS:
                                        if self.options.get(option, False) and CHECKBOX_OPTIONS[option].get("req", False):
                                            extractor_class = CHECKBOX_OPTIONS[option]["extractor"]
                                            extracted_data = extractor_class.extract(page_content)
                                            matched_place[option] = extracted_data

                    for place in unique_places:
                        self.update_data.emit(place)

            await asyncio.sleep(0)

        tasks = [fetch_places(query) for query in self.queries]
        await asyncio.gather(*tasks)


    def stop(self):
        logger.info("Stop requested for scraper worker.")
        self._stop_event.set()
