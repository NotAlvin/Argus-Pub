from dataclasses import dataclass
from datetime import datetime

@dataclass
class NewsArticle:
    publication_date: datetime | None
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
    
    def to_dict(self):
        return {
            "publication_date": str(self.publication_date),
            "title": self.title,
            "link": self.link,
            "content": self.content,
            "summary": self.summary,
            "source": self.source,
            "sentiment": self.sentiment,
            "keywords": self.keywords,
            "categories": self.categories,
            "image": self.image
        }

@dataclass
class SearchQuery:
    names: list[str]
    """Known names of the prospect. There may be multiple, eg ['Dwayne Johnson', 'The Rock']"""
    companies: list[str]
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