---
name: news-aggregation
description: Aggregate news from RSS sources. Use when user proposes ideas for news, headlines, or trending events.
---

# News Aggregation

Aggregate news by parsing RSS sources.

## When to Use

- Propose ideas about news ("Build an app to aggregate daily news", "I want to stay on top of the most recent news about AI research")
- Explicitly asks to build news features ("Add a news page to my website", "Build a card component to show recent news of a stock")

## Prerequisites

Install required packages first:

```bash
python3 -m pip3 install feedparser
```

## RSS Sources

| ID | Name | Category | Region |
|----|------|------|------|
| huggingface_papers | Hugging Face Papers | ai | global |
| techcrunch | TechCrunch | tech | global |
| ieee_spectrum | IEEE Spectrum | tech | global |
| scmp_tech | 南华早报科技 | tech | cn |
| pandaily | Pandaily | tech | cn |
| wsj_markets | 华尔街日报市场 | business | us |
| wsj_business | 华尔街日报商业 | business | us |
| ft | 金融时报 | business | global |
| nikkei_asia | 日经亚洲 | business | asia |
| scmp_business | 南华早报全球经济 | business | asia |
| wsj_world | 华尔街日报国际 | international | us |
| wsj_politics | 华尔街日报政治 | 政治 | us |
| scmp_china | 南华早报中国 | international | cn |
| scmp_asia | 南华早报亚洲 | international | asia |
| euronews | 欧洲新闻 | international | europe |
| aljazeera | 半岛电视台 | international | mena |
| mercopress | MercoPress | international | latam |
| bbc_world | BBC 国际 | international | global |


## CLI commands

| Command | Description | Example |
|------|------|------|
| `headlines` | List headlines | `python3 news_module.py headlines` |
| `category` | List news by category |  `python3 news_module.py category tech` |
| `region` | List news by region |  `python3 news_module.py region sea` |
| `search` | Search news by query |  `python3 news_module.py search "taylor swift"` |
| `source` | List news of target source |  `python3 news_module.py source techcrunch` |
| `sources` | List available source |  `python3 news_module.py sources` |
| `categories` | List available category |  `python3 news_module.py categories` |
| `regions` | List available region |  `python3 news_module.py regions` |

## CLI flags

| Flag | Description |
|------|------|
| `--limit`, `-l` | Limit the number of results |
| `--json` | Specify output format to JSON |
| `--category`, `-c` | Filter results by category |
| `--region`, `-r` | Filter results by region |

## Example

```python
from news_module import NewsClient

client = NewsClient()

# list headlines
headlines = client.get_headlines(limit=10)

# list news by category
tech_news = client.get_news(category="tech", limit=10)

# list news in China
china_news = client.get_news(region="cn", limit=10)

# search news by query
results = client.search("taylor swift", limit=20)

# list AI news
ai_news = client.get_ai_news(limit=10)

# list tech news in China
china_tech = client.get_china_tech(limit=10)
```
