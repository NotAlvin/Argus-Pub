from utils.news_api_template import NewsArticle, SearchQuery
from utils.news_api_utils import check_query, get_query_id, get_sentiment_score, get_summary, save_articles_to_json
from datetime import datetime
from typing import List

import warnings

def get_articles(query: SearchQuery) -> List[NewsArticle]:
    articles = []
    for company in query.names:
        # Step 1: Search entity to get ID of company -> This will take a while - Implement ping every 1 minute
        id = get_query_id(company)
        print(f"Entity {company} query id is: {id}")
        # Step 2: Get articles associated with entity ID
        search_results = check_query(id)
        print(f"Entity {company} search results are: {search_results['data']}")
        if not search_results or "result_en" not in search_results["data"]:
            continue
        if query.language == 'en':
            result_lang = "result_en"
        else:
            result_lang = "result_zh"
        #Step 3: Process articles
        for result in search_results["data"][result_lang]:
            if query.since:
                for article_data in result.get("articles", []):
                    article_info = article_data["article"]
                    if article_info["published"] is not None:
                        publication_date = datetime.strptime(article_info["published"], '%Y-%m-%d')
                        if publication_date > query.since:
                            title = article_info["title"] # Direct map
                            link = article_info["url"] # Direct map
                            content = article_info["text"]  # Direct map
                            if "summary" in article_info and article_info["summary"]:
                                summary = article_info["summary"]
                            else:
                                summary = get_summary(content)
                            source = article_info["source"] # Direct map
                            sentiment = get_sentiment_score(content)
                            keywords = [] ## TODO: Check with LEDR what are keywords
                            categories = []  ## TODO: Check with LEDR what are categories
                            image = None  ## TODO: We need to extract this from somewhere (Can scrape the link)

                            articles.append(NewsArticle(
                            publication_date=publication_date,
                            title=title,
                            link=link,
                            content=content,
                            summary=summary,
                            source=source,
                            sentiment=sentiment,
                            keywords=keywords,
                            categories=categories,
                            image=image
                        ))
            else:
                for article_data in result.get("articles", []):
                    article_info = article_data["article"]
                    if publication_date is not None:
                        publication_date = datetime.strptime(article_info["published"], '%Y-%m-%d') # Direct map
                    else:
                        publication_date = None
                    title = article_info["title"] # Direct map
                    link = article_info["url"] # Direct map
                    content = article_info["text"]  # Direct map
                    if "summary" in article_info and article_info["summary"]:
                        summary = article_info["summary"]
                    else:
                        summary = get_summary(content)
                    source = article_info["source"] # Direct map
                    sentiment = get_sentiment_score(content)
                    keywords = [] ## TODO: ???
                    categories = []  ## TODO: Can get from type?
                    image = None  ## TODO: We need to extract this from somewhere

                    articles.append(NewsArticle(
                        publication_date=publication_date,
                        title=title,
                        link=link,
                        content=content,
                        summary=summary,
                        source=source,
                        sentiment=sentiment,
                        keywords=keywords,
                        categories=categories,
                        image=image
                    ))
    return articles

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    query = SearchQuery(names=["Rosewood Hotels", "New World Development Co Ltd"], language='en', since=datetime(2023, 1, 1))
    articles = get_articles(query)
    save_articles_to_json(articles, 'all_articles.json')