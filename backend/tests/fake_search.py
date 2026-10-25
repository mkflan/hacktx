"""A SearchProvider for tests: canned SerpApi-shaped payloads, no network, call counting."""

YOUTUBE = {
    "video_results": [
        {
            "title": "Build a soil moisture sensor with Arduino",
            "link": "https://www.youtube.com/watch?v=fake0001",
            "thumbnail": {"static": "https://i.ytimg.com/vi/fake0001/hqdefault.jpg"},
            "channel": {"name": "Maker Channel"},
            "published_date": "1 year ago",
            "length": "12:34",
            "description": "Wiring, code and calibration.",
        },
        {"title": "No link here", "channel": {"name": "x"}},
        {
            "title": "Calibrating capacitive sensors",
            "link": "https://www.youtube.com/watch?v=fake0002",
            "thumbnail": {"static": "https://i.ytimg.com/vi/fake0002/hqdefault.jpg"},
            "channel": {"name": "Lab Notes"},
        },
        {
            "title": "Duplicate link",
            "link": "https://www.youtube.com/watch?v=fake0002",
        },
    ]
}

SCHOLAR = {
    "organic_results": [
        {
            "title": "Low-cost capacitive soil moisture sensing: a review",
            "link": "https://example.org/paper/soil-review",
            "snippet": "We review capacitive probes and their calibration.",
            "publication_info": {"summary": "A Author, B Author - Sensors, 2021"},
            "inline_links": {"cited_by": {"total": 42}},
        },
        {"title": "javascript:void(0) is not a link", "link": "javascript:void(0)"},
    ]
}

GOOGLE = {
    "organic_results": [
        {
            "title": "Capacitive Soil Moisture Sensor Guide",
            "link": "https://docs.example.com/soil-moisture",
            "snippet": "Wire VCC to 3.3 V and read A0.",
            "source": "Example Docs",
            "displayed_link": "docs.example.com",
        }
    ]
}

SHOPPING = {
    "shopping_results": [
        {
            "title": "Capacitive Soil Moisture Sensor v1.2 (3 pack)",
            "product_link": "https://shop.example.com/soil-sensor",
            "price": "$8.99",
            "extracted_price": 8.99,
            "source": "Example Shop",
            "thumbnail": "https://shop.example.com/soil.jpg",
        }
    ]
}

PAYLOADS = {
    "youtube": YOUTUBE,
    "google_scholar": SCHOLAR,
    "google": GOOGLE,
    "google_shopping": SHOPPING,
}


class FakeSearch:
    enabled = True

    def __init__(self, payloads=PAYLOADS, fail=None, fail_engines=()):
        self.payloads = payloads
        self.fail = fail  # a SearchError to raise (on every call, or only for fail_engines)
        self.fail_engines = set(fail_engines)
        self.calls: list[tuple[str, str]] = []

    def search(self, engine, query):
        self.calls.append((engine, query))
        if self.fail is not None and (not self.fail_engines or engine in self.fail_engines):
            raise self.fail
        return self.payloads[engine]
