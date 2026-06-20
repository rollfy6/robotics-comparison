from .base import scrape_product_specs, register_parser

try:
    import feedparser
except ImportError:
    feedparser = None

def scrape_rss_news(feed_url, limit=10):
    if feedparser is None:
        return {"error": "feedparser not installed"}
    try:
        feed = feedparser.parse(feed_url)
        entries = []
        for entry in feed.entries[:limit]:
            entries.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", ""),
            })
        return {"entries": entries, "feed_title": feed.feed.get("title", "")}
    except Exception as e:
        return {"error": str(e)}

COMPANY_NEWS_FEEDS = {
    "pickle-robotics": None,
    "locus-robotics": "https://locusrobotics.com/feed/",
    "geekplus": "https://www.geekplus.com/blog/feed",
    "hai-robotics": None,
    "autostore": "https://www.autostoresystem.com/blog/feed",
    "amazon-robotics": "https://www.aboutamazon.com/news/tag/amazon-robotics/rss",
    "symbotic": None,
    "boston-dynamics": "https://www.bostondynamics.com/blog/rss",
    "greyorange": None,
    "exotec": "https://www.exotec.com/en/news/feed",
    "zebra-fetch": "https://www.zebra.com/us/en/home/blog/feed.html",
    "kuka": "https://www.kuka.com/en-us/press/news/feed",
    "mir": "https://www.mobile-industrial-robots.com/news/feed",
    "6-river-systems": "https://ocadointelligentautomation.com/feed",
    "universal-robots": "https://www.universal-robots.com/news/feed",
    "fanuc": None,
    "abb-robotics": "https://new.abb.com/news/rss/robotics",
    "magazino": None,
}
