import sys
import os
from pages.scraper_page import ScraperPage
from pages.settings_page import SettingsPage

class PageManager:
    def __init__(self):
        self.settings_page = SettingsPage()

        self.pages = {
            "scraper_page": ScraperPage(self.settings_page),
            "settings_page": self.settings_page,
        }

        self.base_dir = sys._MEIPASS if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.abspath(__file__))
        self.icon_dir = os.path.join(self.base_dir, 'assets/svg')


    def get_menu_items(self):
        return {
            "scraper_page": {"name": "Scraper", "icon": os.path.join(self.icon_dir, "solid/location-dot.svg")},
            "settings_page": {"name": "Ayarlar", "icon": os.path.join(self.icon_dir, "solid/gear.svg")},
        }
