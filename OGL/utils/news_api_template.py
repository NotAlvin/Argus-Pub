from dataclasses import dataclass
from datetime import datetime

@dataclass
class NewsArticle:
    publication_date: datetime
    title: str
    link: str
    """url"""
    content: str
    summary: str
    source: str
    """
    Name of the news source
    """
    sentiment: float
    """
    range [-1; 1]
    -1 is the most negative, 0 is neutral, 1 is the most positive
    """
    keywords: list[str]
    categories: list[str]
    image: str | None
    """
    URL to an image of the news article.
    No restrictions on the format of the image.
    """

@dataclass
class SearchQuery:
    names: list[str]
    """Known companies the prospect is associated with"""
    language: str
    """
    Language we want the news articles to be in.
    Possible values: 'en' (english), 'zh-cn' (Simplified chinese), 'zh-tw' (Traditional chinese)
    """
    since: datetime | None
    """
    If provided, only news articles published after this date will be returned.
    """

def get_articles(query: SearchQuery) -> list[NewsArticle]:
    pass