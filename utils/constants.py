from utils.fetch_utils import (
    EmailExtractor,
    FacebookExtractor,
    InstagramExtractor,
    YoutubeExtractor,
    LinkedinExtractor,
    TwitterExtractor,
    TiktokExtractor
)

CHECKBOX_OPTIONS = {
    "title": {
        'label': "İşletme Adı",
        'description': "İşletme Adını Çek"
    },
    "phone_number": {
        'label': "Telefon Numarası",
        'description': "Telefon Numarasını Çek"
    },
    "url": {
        'label': "Website",
        'description': "Website Çek"
    },
    "rating_score": {
        'label': "Puan",
        'description': "Puan Çek"
    },
    "review_count": {
        'label': "Yorum Sayısı",
        'description': "Yorum Sayısı Çek"
    },
    "address": {
        'label': "İşletme Adresi",
        'description': "İşletme Adresi Çek"
    },
    "category": {
        "label": "Kategori",
        "description": "Kategorileri Çek",
    },
    "mail": {
        "label": "Mail",
        "description": "Mailleri Çek",
        "req": True,
        "extractor": EmailExtractor
    },
    "instagram": {
        "label": "Instagram",
        "description": "Instagram Çek",
        "req": True,
        "extractor": InstagramExtractor
    },
    "facebook": {
        "label": "Facebook",
        "description": "Facebook Çek",
        "req": True,
        "extractor": FacebookExtractor
    },
    "youtube": {
        "label": "YouTube",
        "description": "YouTube Çek",
        "req": True,
        "extractor": YoutubeExtractor
    },
    "linkedin": {
        "label": "LinkedIn",
        "description": "LinkedIn Çek",
        "req": True,
        "extractor": LinkedinExtractor
    },
    "twitter": {
        "label": "Twitter",
        "description": "Twitter Çek",
        "req": True,
        "extractor": TwitterExtractor
    },
    "tiktok": {
        "label": "TikTok",
        "description": "TikTok Çek",
        "req": True,
        "extractor": TiktokExtractor
    },
}