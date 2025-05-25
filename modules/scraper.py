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
            response = await self.session.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            return response.text
        except asyncio.TimeoutError:
            logger.error(f"Timeout error for {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching data from {url}: {e}")
            return None

    async def fetch_category_data(self, feature_id):
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
        params = {
            "q": self.query,
            "start": self.start,
            "hl": "en",
            "gl": "en",
            "client": "earth-client",
            "cv": "7.3.6.9796",
            "useragent": self.headers['User-Agent'],
            "output": "xml"
        }
        xml_data = await self.fetch_data(self.BASE_URL, params)
        return self.parse_xml(xml_data)

    def parse_category_html(self, html_data):
        if not html_data:
            return None
        soup = bs(html_data, 'html.parser')
        category_span = soup.find("span", class_="Qfo35d")
        return category_span.text if category_span else None
    
    def parse_lat_long_html(self, html_data):
        if not html_data:
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
            places_data = []
            
            omnibox_content = root.find(".//omnibox_content")
            more_places_available = False
            if omnibox_content is not None:
                more_places_available = omnibox_content.get('more_place_cards_available') == 'true'

            for place_card in root.findall(".//place_card"):
                title_elem = place_card.find("title")
                title = title_elem.text if title_elem is not None else "Unknown"
                
                address_lines = [line.text for line in place_card.findall("address_line") if line.text]
                address = " ".join(address_lines) or None
                
                phone_number_elem = place_card.find("phone_number")
                phone_number = phone_number_elem.text if phone_number_elem is not None else None
                
                feature_id_elem = place_card.find("feature_id")
                feature_id = feature_id_elem.text if feature_id_elem is not None else None
                
                url = None
                authority_page_link_elem = place_card.find("authority_page_link")
                if authority_page_link_elem is not None:
                    url_elem = authority_page_link_elem.find("url")
                    if url_elem is not None and url_elem.text:
                        raw_url = url_elem.text
                        url_parts = raw_url.split("/url?q=")
                        if len(url_parts) > 1:
                            url = unquote(url_parts[-1].split("&opi=")[0])

                rating_score = 0.0
                review_count = 0
                rating_elem = place_card.find("rating")
                if rating_elem is not None:
                    rating_score_attr = rating_elem.get("num_rating_stars")
                    rating_score = float(rating_score_attr) if rating_score_attr else 0.0
                    
                    review_count_anchor = rating_elem.find(".//review_count/anchor_text")
                    if review_count_anchor is not None and review_count_anchor.text:
                        review_count_text = review_count_anchor.text.split()[0]
                        try:
                            review_count = int(review_count_text.replace(',', '').strip())
                        except ValueError:
                            review_count = 0
                
                places_data.append({
                    "title": title,
                    "address": address,
                    "phone_number": phone_number,
                    "feature_id": feature_id,
                    "url": url,
                    "rating_score": rating_score,
                    "review_count": review_count
                })
            
            logger.info(f"Successfully parsed {len(places_data)} places.")
            return places_data, more_places_available
        except ET.ParseError as e:
            logger.error(f"Error parsing XML data (ParseError): {e}. Data: {xml_data[:200]}...")
            return [], False
        except Exception as e:
            logger.error(f"Error parsing XML data: {e}", exc_info=True)
            return [], False


class ScraperWorker(QThread):
    update_data = Signal(dict)
    finished = Signal()
    query_progress = Signal(str, int, int)

    def __init__(self, queries, options=None, max_concurrent_requests=30):
        super().__init__()
        self.queries = queries
        self.options = options if options is not None else {}
        self.query_semaphore = asyncio.Semaphore(max_concurrent_requests)
        self._stop_event = asyncio.Event()
        self.session = None
        self.global_seen_feature_ids = set()

    def run(self):
        logger.info("Starting scraper worker thread.")
        try:
            asyncio.run(self.scrape())
        except Exception as e:
            logger.error(f"Error in scraper worker: {e}", exc_info=True)
        finally:
            self.finished.emit()
            logger.info("Scraper worker thread finished.")

    async def scrape(self):
        self.session = fetch_utils.create_client()
        try:
            tasks = []
            for i, query in enumerate(self.queries):
                if self._stop_event.is_set():
                    break
                task = asyncio.create_task(self.fetch_places_for_query(query, i + 1, len(self.queries)))
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
                
        finally:
            if self.session:
                logger.info("Closing HTTP session.")
                await self.session.aclose()
                self.session = None
            logger.info("Scraping process completed.")

    async def fetch_places_for_query(self, query, query_num, total_queries):
        async with self.query_semaphore:
            if self._stop_event.is_set():
                return

            logger.info(f"Processing query {query_num}/{total_queries}: {query}")
            client = GoogleEarthClient(query, self.session)
            more_pages_exist = True
            current_start_index = 0
            total_processed_for_query = 0
            consecutive_empty_batches = 0

            while more_pages_exist and consecutive_empty_batches < 3:
                if self._stop_event.is_set():
                    return

                try:
                    batch_fetch_tasks = []
                    max_offset_step_for_parallel = 50
                    offset_fetch_step = 10
                    
                    for i in range(0, max_offset_step_for_parallel, offset_fetch_step):
                        task = asyncio.create_task(
                            GoogleEarthClient(query, self.session, current_start_index + i).get_places()
                        )
                        batch_fetch_tasks.append(task)
                    
                    batch_results = await asyncio.gather(*batch_fetch_tasks, return_exceptions=True)
                    
                    all_places_from_batch = []
                    any_batch_has_more = False
                    
                    for result in batch_results:
                        if self._stop_event.is_set():
                            return

                        if isinstance(result, tuple) and len(result) == 2:
                            places, more_available = result
                            if places:
                                all_places_from_batch.extend(places)
                                any_batch_has_more = any_batch_has_more or more_available
                                consecutive_empty_batches = 0
                            else:
                                consecutive_empty_batches += 1
                        elif isinstance(result, Exception):
                            logger.error(f"Error in batch get_places for query '{query}': {result}")
                            consecutive_empty_batches += 1
                        else:
                            consecutive_empty_batches += 1
                    
                    more_pages_exist = any_batch_has_more
                    
                    if not all_places_from_batch:
                        logger.warning(f"No places found for query: {query} at start_index: {current_start_index}. Consecutive empty: {consecutive_empty_batches}")
                        if not more_pages_exist:
                            break
                        current_start_index += offset_fetch_step * (max_offset_step_for_parallel // offset_fetch_step)
                        continue
                    
                    current_start_index += len(all_places_from_batch)
                    
                    unique_places_to_process = []
                    for place in all_places_from_batch:
                        feature_id = place.get("feature_id")
                        if feature_id and feature_id not in self.global_seen_feature_ids:
                            unique_places_to_process.append(place)
                            self.global_seen_feature_ids.add(feature_id)

                    if not unique_places_to_process:
                        logger.info(f"No new unique places found for query: {query}")
                        if not more_pages_exist:
                            break
                        continue

                    logger.info(f"Found {len(unique_places_to_process)} unique new places for query: {query}")

                    await self.fetch_and_process_additional_info(unique_places_to_process, client)

                    for place_data in unique_places_to_process:
                        if self._stop_event.is_set():
                            return
                        self.update_data.emit(place_data)
                        total_processed_for_query += 1

                    self.query_progress.emit(query, total_processed_for_query, current_start_index)
                    
                except Exception as e:
                    logger.error(f"Error processing query '{query}' around start_index {current_start_index}: {e}", exc_info=True)
                    consecutive_empty_batches += 1
                    continue
            logger.info(f"Finished processing query: {query}. Total processed: {total_processed_for_query}")


    async def fetch_and_process_additional_info(self, places, client):
        parse_category = self.options.get("category", False)
        parse_lat_long = self.options.get("lat_long", False)
        
        needs_feature_data = parse_category or parse_lat_long
        if needs_feature_data:
            await self._fetch_feature_details(places, client, parse_category, parse_lat_long)

        needs_url_data = any(self.options.get(opt, False) for opt in CHECKBOX_OPTIONS if CHECKBOX_OPTIONS[opt].get("req", False))
        if needs_url_data:
            await self._fetch_url_based_details(places)

    async def _fetch_feature_details(self, places, client, parse_category, parse_lat_long):
        batch_size = 50
        for i in range(0, len(places), batch_size):
            if self._stop_event.is_set():
                return
            
            current_batch = places[i:i + batch_size]
            feature_tasks = [client.fetch_category_data(place.get("feature_id")) for place in current_batch]
            results = await asyncio.gather(*feature_tasks, return_exceptions=True)
            
            for place, html_content in zip(current_batch, results):
                if self._stop_event.is_set():
                    return
                if isinstance(html_content, str):
                    if parse_category:
                        place['category'] = client.parse_category_html(html_content)
                    if parse_lat_long:
                        place['lat_long'] = client.parse_lat_long_html(html_content)
                elif isinstance(html_content, Exception):
                    logger.error(f"Error fetching feature data for {place.get('feature_id')}: {html_content}")

    async def _fetch_url_based_details(self, places):
        places_with_url = [p for p in places if p.get("url")]
        if not places_with_url:
            return

        batch_size = 30
        for i in range(0, len(places_with_url), batch_size):
            if self._stop_event.is_set():
                return

            current_batch = places_with_url[i:i + batch_size]
            url_fetch_tasks = [
                fetch_utils.fetch_url(self.session, place.get("url"), place.get("feature_id")) 
                for place in current_batch
            ]
            page_content_results = await asyncio.gather(*url_fetch_tasks, return_exceptions=True)

            for place, result in zip(current_batch, page_content_results):
                if self._stop_event.is_set():
                    return
                
                if isinstance(result, tuple) and len(result) == 2 and result[0]:
                    page_content = result[0]
                    for option_key in CHECKBOX_OPTIONS:
                        if self.options.get(option_key, False) and CHECKBOX_OPTIONS[option_key].get("req", False):
                            try:
                                extractor_class = CHECKBOX_OPTIONS[option_key]["extractor"]
                                extracted_data = extractor_class.extract(page_content)
                                place[option_key] = extracted_data
                            except Exception as e:
                                logger.error(f"Error extracting {option_key} for {place.get('feature_id')}: {e}")
                elif isinstance(result, Exception):
                     logger.error(f"Error fetching URL {place.get('url')} for {place.get('feature_id')}: {result}")


    def stop(self):
        logger.info("Stop requested for scraper worker.")
        self._stop_event.set()
