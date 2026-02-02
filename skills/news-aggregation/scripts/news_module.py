#!/usr/bin/env python3
"""
News Module for ChatGPT Skills
Comprehensive news aggregation from RSS feeds (No Google News)

Data Sources:
- tech: TechCrunch, IEEE Spectrum, MIT Tech Review, SCMP Tech, Pandaily
- AI Research: OpenAI, Hugging Face Papers
- Business & Markets: WSJ, Financial Times, Nikkei Asia
- Regional: SCMP (Asia/China), Euronews, Al Jazeera, MercoPress, BBC World

Usage:
    from news_module import NewsClient

    client = NewsClient()

    # Get top headlines (aggregated from all sources)
    news = client.get_headlines()

    # Get news by category
    news = client.get_news(category="tech")
    news = client.get_news(category="ai")

    # Get news by region
    news = client.get_news(region="asia")
    news = client.get_news(region="china")

    # Search news (searches across all RSS sources)
    news = client.search("artificial intelligence")

    # Get news from specific source
    news = client.get_source("techcrunch")

Command Line:
    python3 news_module.py headlines
    python3 news_module.py category tech
    python3 news_module.py category ai
    python3 news_module.py region asia
    python3 news_module.py search "AI"
    python3 news_module.py source techcrunch
    python3 news_module.py sources
"""

import json
import urllib.request
import urllib.parse
import html
import re
from datetime import datetime
from typing import Optional, List, Dict
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import feedparser

    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    print("Warning: feedparser not installed. Run: pip3 install feedparser")


class MLStripper(HTMLParser):
    """Strip HTML tags from text"""

    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return "".join(self.fed)


def strip_html(text):
    """Remove HTML tags from text"""
    if not text:
        return ""
    s = MLStripper()
    try:
        s.feed(html.unescape(text))
        return s.get_data()
    except (ValueError, TypeError, AssertionError):
        # Fallback to regex if HTML parsing fails
        return re.sub("<[^<]+?>", "", text)


class NewsClient:
    """News client using RSS feeds from global sources"""

    # ==========================================================================
    # RSS FEED SOURCES - Organized by Category and Region
    # ==========================================================================

    SOURCES = {
        # ----------------------------------------------------------------------
        # tech - Western
        # ----------------------------------------------------------------------
        "techcrunch": {
            "name": "TechCrunch",
            "url": "https://techcrunch.com/feed/",
            "language": "en",
            "category": "tech",
            "region": "western",
            "tags": ["tech", "startups", "venture"],
        },
        "ieee_spectrum": {
            "name": "IEEE Spectrum",
            "url": "https://spectrum.ieee.org/customfeeds/feed/all-topics/rss",
            "language": "en",
            "category": "tech",
            "region": "western",
            "tags": ["tech", "engineering", "science"],
        },
        # ----------------------------------------------------------------------
        # AI RESEARCH
        # ----------------------------------------------------------------------
        "huggingface_papers": {
            "name": "Hugging Face Papers (Daily AI)",
            "url": "https://papers.takara.ai/api/feed",
            "language": "en",
            "category": "ai",
            "region": "global",
            "tags": ["ai", "research", "papers", "ml"],
        },
        # ----------------------------------------------------------------------
        # BUSINESS, POLICY & MARKETS - USA
        # ----------------------------------------------------------------------
        "wsj_markets": {
            "name": "WSJ Markets",
            "url": "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain",
            "language": "en",
            "category": "business",
            "region": "usa",
            "tags": ["business", "markets", "finance"],
        },
        "wsj_business": {
            "name": "WSJ US Business",
            "url": "https://feeds.content.dowjones.io/public/rss/WSJcomUSBusiness",
            "language": "en",
            "category": "business",
            "region": "usa",
            "tags": ["business", "economy"],
        },
        "wsj_politics": {
            "name": "WSJ Politics",
            "url": "https://feeds.content.dowjones.io/public/rss/socialpoliticsfeed",
            "language": "en",
            "category": "politics",
            "region": "usa",
            "tags": ["politics", "policy"],
        },
        "wsj_world": {
            "name": "WSJ World News",
            "url": "https://feeds.content.dowjones.io/public/rss/RSSWorldNews",
            "language": "en",
            "category": "world",
            "region": "usa",
            "tags": ["world", "international"],
        },
        # ----------------------------------------------------------------------
        # BUSINESS, POLICY & MARKETS - Western/Europe
        # ----------------------------------------------------------------------
        "ft": {
            "name": "Financial Times",
            "url": "https://www.ft.com/business-education?format=rss",
            "language": "en",
            "category": "business",
            "region": "western",
            "tags": ["business", "finance", "education"],
        },
        "euronews": {
            "name": "Euronews Europe",
            "url": "https://www.euronews.com/rss?format=mrss&level=vertical&name=my-europe",
            "language": "en",
            "category": "world",
            "region": "europe",
            "tags": ["europe", "politics", "news"],
        },
        # ----------------------------------------------------------------------
        # ASIA - China & Greater China
        # ----------------------------------------------------------------------
        "scmp_tech": {
            "name": "SCMP Big Tech",
            "url": "https://www.scmp.com/rss/320663/feed",
            "language": "en",
            "category": "tech",
            "region": "china",
            "tags": ["china", "tech", "asia"],
        },
        "scmp_china": {
            "name": "SCMP China",
            "url": "https://www.scmp.com/rss/4/feed/",
            "language": "en",
            "category": "world",
            "region": "china",
            "tags": ["china", "politics", "economy"],
        },
        "scmp_asia": {
            "name": "SCMP Asia",
            "url": "https://www.scmp.com/rss/3/feed/",
            "language": "en",
            "category": "world",
            "region": "asia",
            "tags": ["asia", "politics", "economy"],
        },
        "scmp_business": {
            "name": "SCMP Global Economy",
            "url": "https://www.scmp.com/rss/12/feed/",
            "language": "en",
            "category": "business",
            "region": "asia",
            "tags": ["asia", "business", "economy", "markets"],
        },
        "pandaily": {
            "name": "Pandaily",
            "url": "https://pandaily.com/feed",
            "language": "en",
            "category": "tech",
            "region": "china",
            "tags": ["china", "tech", "startups", "ai"],
        },
        # ----------------------------------------------------------------------
        # ASIA - East Asia (Japan, Korea)
        # ----------------------------------------------------------------------
        "nikkei_asia": {
            "name": "Nikkei Asia",
            "url": "https://asia.nikkei.com/rss/feed/nar",
            "language": "en",
            "category": "business",
            "region": "asia",
            "tags": ["asia", "japan", "business", "economy"],
        },
        # ----------------------------------------------------------------------
        # MIDDLE EAST & NORTH AFRICA (MENA)
        # ----------------------------------------------------------------------
        "aljazeera": {
            "name": "Al Jazeera",
            "url": "https://www.aljazeera.com/xml/rss/all.xml",
            "language": "en",
            "category": "world",
            "region": "mena",
            "tags": ["middle_east", "world", "politics"],
        },
        # ----------------------------------------------------------------------
        # LATIN AMERICA (LATAM)
        # ----------------------------------------------------------------------
        "mercopress": {
            "name": "MercoPress",
            "url": "https://en.mercopress.com/rss/",
            "language": "en",
            "category": "world",
            "region": "latam",
            "tags": ["latin_america", "politics", "economy"],
        },
        # ----------------------------------------------------------------------
        # GENERAL NEWS - Global
        # ----------------------------------------------------------------------
        "bbc_world": {
            "name": "BBC World",
            "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
            "language": "en",
            "category": "world",
            "region": "western",
            "tags": ["world", "international"],
        },
        # ----------------------------------------------------------------------
        # GENERAL NEWS - SEA
        # ----------------------------------------------------------------------
        "st": {
            "name": "The Straits Times",
            "url": "https://www.straitstimes.com/news/world/rss.xml",
            "language": "en",
            "category": "world",
            "region": "sea",
            "tags": ["world", "international", "sea", "singapore"],
        },
        "cna": {
            "name": "Channel NewsAsia",
            "url": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml",
            "language": "en",
            "category": "world",
            "region": "sea",
            "tags": ["world", "international", "sea", "singapore"],
        },
    }

    # ==========================================================================
    # CATEGORY MAPPINGS
    # ==========================================================================

    CATEGORIES = {
        "tech": ["techcrunch", "ieee_spectrum", "scmp_tech", "pandaily"],
        "ai": ["huggingface_papers"],
        "business": ["wsj_markets", "wsj_business", "ft", "nikkei_asia", "scmp_business"],
        "politics": ["wsj_politics"],
        "world": ["wsj_world", "bbc_world", "euronews", "scmp_asia", "scmp_china", "aljazeera", "mercopress"],
        "science": ["ieee_spectrum"],
    }

    # ==========================================================================
    # REGION MAPPINGS
    # ==========================================================================

    REGIONS = {
        "usa": ["wsj_markets", "wsj_business", "wsj_politics", "wsj_world"],
        "western": ["techcrunch", "ieee_spectrum", "ft", "bbc_world"],
        "europe": ["euronews", "ft", "bbc_world"],
        "asia": ["scmp_asia", "nikkei_asia", "scmp_tech", "scmp_china", "scmp_business", "pandaily"],
        "china": ["scmp_tech", "scmp_china", "pandaily"],
        "mena": ["aljazeera"],
        "latam": ["mercopress"],
        "global": ["huggingface_papers"],
    }

    def __init__(self, language: str = "en", timeout: int = 15):
        """
        Initialize news client

        Args:
            language: Default language (currently only "en" supported)
            timeout: Request timeout in seconds
        """
        if not HAS_FEEDPARSER:
            raise ImportError("feedparser not installed. Run: pip3 install feedparser")

        self.language = language
        self.timeout = timeout

    def _fetch_feed(self, url: str, limit: int = 20, source_name: str = "") -> List[Dict]:
        """Fetch and parse RSS feed with timeout"""
        try:
            # Use urllib with timeout, then parse with feedparser
            req = urllib.request.Request(url, headers={"User-Agent": "NewsModule/2.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                content = response.read()
            feed = feedparser.parse(content)

            articles = []

            for entry in feed.entries[:limit]:
                # Parse published date
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        published = datetime(*entry.published_parsed[:6]).isoformat()
                    except (TypeError, ValueError):
                        pass
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    try:
                        published = datetime(*entry.updated_parsed[:6]).isoformat()
                    except (TypeError, ValueError):
                        pass

                # Get description/summary
                description = ""
                if hasattr(entry, "summary"):
                    description = strip_html(entry.summary)[:500]
                elif hasattr(entry, "description"):
                    description = strip_html(entry.description)[:500]

                articles.append(
                    {
                        "title": strip_html(entry.get("title", "")),
                        "link": entry.get("link", ""),
                        "description": description,
                        "published": published,
                        "source": source_name or feed.feed.get("title", ""),
                    }
                )

            return articles
        except Exception as e:
            return [{"error": str(e), "source": source_name}]

    def _fetch_multiple_feeds(self, source_ids: List[str], limit_per_source: int = 10) -> List[Dict]:
        """Fetch multiple feeds in parallel"""
        all_articles = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for source_id in source_ids:
                source = self.SOURCES.get(source_id)
                if source:
                    future = executor.submit(self._fetch_feed, source["url"], limit_per_source, source["name"])
                    futures[future] = source_id

            for future in as_completed(futures):
                source_id = futures[future]
                try:
                    articles = future.result()
                    for article in articles:
                        if "error" not in article:
                            article["source_id"] = source_id
                            all_articles.append(article)
                except (OSError, TimeoutError, ValueError):
                    # Network errors or parsing errors - skip this source
                    pass

        # Sort by date
        all_articles.sort(key=lambda x: x.get("published") or "", reverse=True)
        return all_articles

    def get_headlines(self, limit: int = 20, language: Optional[str] = None) -> Dict:
        """
        Get top headlines from all RSS sources

        Args:
            limit: Number of articles
            language: Reserved for future use (currently all sources are English)

        Returns:
            Dict with articles
        """
        language = language or self.language

        # Fetch from all sources and aggregate
        all_source_ids = list(self.SOURCES.keys())
        limit_per_source = max(3, limit // len(all_source_ids) + 1)

        articles = self._fetch_multiple_feeds(all_source_ids, limit_per_source)

        # Sort by published date (newest first)
        articles.sort(key=lambda x: x.get("published") or "", reverse=True)

        sources_used = [self.SOURCES[sid]["name"] for sid in all_source_ids]

        return {
            "type": "headlines",
            "language": language,
            "sources": sources_used,
            "count": len(articles[:limit]),
            "articles": articles[:limit],
        }

    def get_news(
        self,
        category: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 20,
        language: Optional[str] = None,
    ) -> Dict:
        """
        Get news by category and/or region

        Args:
            category: News category (tech, ai, business, world, etc.)
            region: Region filter (usa, western, europe, asia, china, mena, latam)
            limit: Number of articles
            language: Reserved for future use (currently all sources are English)

        Returns:
            Dict with articles
        """
        language = language or self.language

        # Determine source list
        source_ids = set()

        if category:
            category = category.lower()
            if category in self.CATEGORIES:
                source_ids.update(self.CATEGORIES[category])
            else:
                # Invalid category
                return {
                    "error": f"Unknown category: {category}",
                    "available_categories": sorted(self.CATEGORIES.keys()),
                }

        if region:
            region = region.lower()
            if region in self.REGIONS:
                if source_ids:
                    # Intersection with category
                    source_ids = source_ids.intersection(set(self.REGIONS[region]))
                else:
                    source_ids = set(self.REGIONS[region])
            else:
                # Invalid region
                return {"error": f"Unknown region: {region}", "available_regions": list(self.REGIONS.keys())}

        if not source_ids:
            # Default to tech sources (when no category/region specified)
            source_ids = set(self.CATEGORIES.get("tech", ["techcrunch", "scmp_tech"]))

        # Calculate limit per source
        limit_per_source = max(5, limit // len(source_ids) + 2)

        # Fetch from multiple sources in parallel
        articles = self._fetch_multiple_feeds(list(source_ids), limit_per_source)

        # Get source names
        sources_used = [self.SOURCES[sid]["name"] for sid in source_ids if sid in self.SOURCES]

        return {
            "type": "category" if category else "region",
            "category": category,
            "region": region,
            "language": language,
            "sources": sources_used,
            "count": len(articles[:limit]),
            "articles": articles[:limit],
        }

    def search(self, query: str, limit: int = 20, language: Optional[str] = None) -> Dict:
        """
        Search news across all RSS sources

        Args:
            query: Search query
            limit: Number of results
            language: Reserved for future use (currently all sources are English)

        Returns:
            Dict with articles matching the query
        """
        language = language or self.language
        query_lower = query.lower()

        # Fetch from all sources
        all_source_ids = list(self.SOURCES.keys())
        all_articles = self._fetch_multiple_feeds(all_source_ids, limit_per_source=10)

        # Filter articles by query (search in title and description)
        matching_articles = []
        for article in all_articles:
            title = article.get("title", "").lower()
            description = article.get("description", "").lower()
            if query_lower in title or query_lower in description:
                matching_articles.append(article)

        # Sort by date (newest first) - title matches will naturally be more relevant
        matching_articles.sort(key=lambda x: x.get("published") or "", reverse=True)

        return {
            "type": "search",
            "query": query,
            "language": language,
            "count": len(matching_articles[:limit]),
            "articles": matching_articles[:limit],
        }

    def get_source(self, source_id: str, limit: int = 20) -> Dict:
        """
        Get news from specific source

        Args:
            source_id: Source identifier (e.g., "techcrunch", "scmp_tech")
            limit: Number of articles

        Returns:
            Dict with articles
        """
        source_id = source_id.lower()

        if source_id not in self.SOURCES:
            return {"error": f"Unknown source: {source_id}", "available_sources": list(self.SOURCES.keys())}

        source = self.SOURCES[source_id]
        articles = self._fetch_feed(source["url"], limit, source["name"])

        return {
            "type": "source",
            "source": source["name"],
            "source_id": source_id,
            "url": source.get("url"),
            "language": source.get("language"),
            "category": source.get("category"),
            "region": source.get("region"),
            "tags": source.get("tags", []),
            "count": len([a for a in articles if "error" not in a]),
            "articles": articles,
        }

    def list_sources(
        self, language: Optional[str] = None, category: Optional[str] = None, region: Optional[str] = None
    ) -> List[Dict]:
        """
        List available news sources

        Args:
            language: Filter by language
            category: Filter by category
            region: Filter by region

        Returns:
            List of sources
        """
        sources = []
        for source_id, source in self.SOURCES.items():
            if language and source.get("language") != language:
                continue
            if category and source.get("category") != category:
                continue
            if region and source.get("region") != region:
                continue
            sources.append(
                {
                    "id": source_id,
                    "name": source["name"],
                    "url": source["url"],
                    "language": source.get("language"),
                    "category": source.get("category"),
                    "region": source.get("region"),
                    "tags": source.get("tags", []),
                }
            )
        return sources

    def list_categories(self) -> List[str]:
        """List available categories"""
        return sorted(self.CATEGORIES.keys())

    def list_regions(self) -> List[str]:
        """List available regions"""
        return sorted(self.REGIONS.keys())

    def get_ai_news(self, limit: int = 20) -> Dict:
        """
        Get AI-related news from multiple sources

        Shortcut for getting AI research and tech news
        """
        return self.get_news(category="ai", limit=limit)

    def get_china_tech(self, limit: int = 20) -> Dict:
        """
        Get China tech news

        Shortcut for getting China tech news from SCMP and Pandaily
        """
        return self.get_news(category="tech", region="china", limit=limit)


def main():
    """Command line interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description="News Module - ChatGPT Skills",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 news_module.py headlines
  python3 news_module.py category tech
  python3 news_module.py category ai
  python3 news_module.py region china
  python3 news_module.py region asia
  python3 news_module.py search "artificial intelligence"
  python3 news_module.py source techcrunch
  python3 news_module.py sources --category tech
  python3 news_module.py sources --region china
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Headlines
    headlines_parser = subparsers.add_parser("headlines", help="Get top headlines")
    headlines_parser.add_argument("--limit", "-l", type=int, default=10)
    headlines_parser.add_argument("--language", default="en", help="Language (currently only 'en' supported)")
    headlines_parser.add_argument("--json", action="store_true")

    # Category
    category_parser = subparsers.add_parser("category", help="Get news by category")
    category_parser.add_argument("name", help="Category name (tech, ai, business, world, science)")
    category_parser.add_argument("--region", "-r", help="Filter by region")
    category_parser.add_argument("--limit", "-l", type=int, default=10)
    category_parser.add_argument("--language", default="en", help="Language (currently only 'en' supported)")
    category_parser.add_argument("--json", action="store_true")

    # Region
    region_parser = subparsers.add_parser("region", help="Get news by region")
    region_parser.add_argument("name", help="Region name (usa, western, europe, asia, china, mena, latam)")
    region_parser.add_argument("--category", "-c", help="Filter by category")
    region_parser.add_argument("--limit", "-l", type=int, default=10)
    region_parser.add_argument("--json", action="store_true")

    # Search
    search_parser = subparsers.add_parser("search", help="Search news")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", "-l", type=int, default=10)
    search_parser.add_argument("--language", default="en", help="Language (currently only 'en' supported)")
    search_parser.add_argument("--json", action="store_true")

    # Source
    source_parser = subparsers.add_parser("source", help="Get news from source")
    source_parser.add_argument("name", help="Source ID")
    source_parser.add_argument("--limit", "-l", type=int, default=10)
    source_parser.add_argument("--json", action="store_true")

    # Sources list
    sources_parser = subparsers.add_parser("sources", help="List available sources")
    sources_parser.add_argument("--language", help="Language filter")
    sources_parser.add_argument("--category", "-c")
    sources_parser.add_argument("--region", "-r")

    # Categories list
    subparsers.add_parser("categories", help="List categories")

    # Regions list
    subparsers.add_parser("regions", help="List regions")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    client = NewsClient()

    if args.command == "headlines":
        result = client.get_headlines(limit=args.limit, language=args.language)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\n{'=' * 70}")
            print(f"  TOP HEADLINES (from {len(client.SOURCES)} RSS sources)")
            print(f"{'=' * 70}")
            for i, article in enumerate(result["articles"], 1):
                if "error" in article:
                    continue
                title = article["title"][:65] + "..." if len(article["title"]) > 65 else article["title"]
                print(f"\n  {i}. {title}")
                print(f"     Source: {article.get('source', 'N/A')}")
                if article.get("published"):
                    print(f"     [{article['published'][:10]}]")
                print(f"     {article['link'][:70]}")

    elif args.command == "category":
        result = client.get_news(category=args.name, region=args.region, limit=args.limit, language=args.language)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif "error" in result:
            print(f"Error: {result['error']}")
            if result.get("available_categories"):
                print(f"\nAvailable categories: {', '.join(result['available_categories'])}")
        else:
            print(f"\n{'=' * 70}")
            print(f"  {args.name.upper()} NEWS")
            if result.get("sources"):
                print(f"  Sources: {', '.join(result['sources'][:5])}")
            print(f"{'=' * 70}")
            for i, article in enumerate(result["articles"], 1):
                if "error" in article:
                    continue
                title = article["title"][:65] + "..." if len(article["title"]) > 65 else article["title"]
                print(f"\n  {i}. {title}")
                print(f"     Source: {article.get('source', 'N/A')}")
                print(f"     {article['link'][:70]}")

    elif args.command == "region":
        result = client.get_news(region=args.name, category=args.category, limit=args.limit)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif "error" in result:
            print(f"Error: {result['error']}")
            if result.get("available_regions"):
                print(f"\nAvailable regions: {', '.join(result['available_regions'])}")
        else:
            print(f"\n{'=' * 70}")
            print(f"  {args.name.upper()} REGION NEWS")
            if result.get("sources"):
                print(f"  Sources: {', '.join(result['sources'][:5])}")
            print(f"{'=' * 70}")
            for i, article in enumerate(result["articles"], 1):
                if "error" in article:
                    continue
                title = article["title"][:65] + "..." if len(article["title"]) > 65 else article["title"]
                print(f"\n  {i}. {title}")
                print(f"     Source: {article.get('source', 'N/A')}")
                print(f"     {article['link'][:70]}")

    elif args.command == "search":
        result = client.search(args.query, limit=args.limit, language=args.language)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\n{'=' * 70}")
            print(f"  SEARCH: '{args.query}'")
            print(f"  Found: {result['count']} articles")
            print(f"{'=' * 70}")
            for i, article in enumerate(result["articles"], 1):
                if "error" in article:
                    continue
                title = article["title"][:65] + "..." if len(article["title"]) > 65 else article["title"]
                print(f"\n  {i}. {title}")
                print(f"     {article['link'][:70]}")

    elif args.command == "source":
        result = client.get_source(args.name, limit=args.limit)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif "error" in result:
            print(f"Error: {result['error']}")
            if "available_sources" in result:
                print(f"\nAvailable sources: {', '.join(result['available_sources'][:10])}...")
        else:
            print(f"\n{'=' * 70}")
            print(f"  {result['source']}")
            print(f"  Category: {result.get('category', 'N/A')} | Region: {result.get('region', 'N/A')}")
            print(f"  Tags: {', '.join(result.get('tags', []))}")
            print(f"{'=' * 70}")
            for i, article in enumerate(result["articles"], 1):
                if "error" in article:
                    continue
                title = article["title"][:65] + "..." if len(article["title"]) > 65 else article["title"]
                print(f"\n  {i}. {title}")
                if article.get("published"):
                    print(f"     [{article['published'][:10]}]")
                print(f"     {article['link'][:70]}")

    elif args.command == "sources":
        sources = client.list_sources(language=args.language, category=args.category, region=args.region)
        print(f"\n{'=' * 90}")
        print(f"  AVAILABLE SOURCES ({len(sources)} total)")
        print(f"{'=' * 90}")
        print(f"  {'ID':<20} {'Name':<25} {'Category':<12} {'Region':<10} {'Tags'}")
        print(f"  {'-' * 85}")
        for s in sources:
            tags = ", ".join(s.get("tags", [])[:3])
            print(f"  {s['id']:<20} {s['name']:<25} {s.get('category', '-'):<12} {s.get('region', '-'):<10} {tags}")

    elif args.command == "categories":
        categories = client.list_categories()
        print("\nAvailable Categories:")
        print("=" * 40)
        for cat in categories:
            sources = client.CATEGORIES.get(cat, [])
            print(f"  {cat:<15} ({len(sources)} sources)")

    elif args.command == "regions":
        regions = client.list_regions()
        print("\nAvailable Regions:")
        print("=" * 40)
        for region in regions:
            sources = client.REGIONS.get(region, [])
            print(f"  {region:<15} ({len(sources)} sources)")


if __name__ == "__main__":
    main()
