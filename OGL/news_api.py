from OGL.utils.news_api_template import NewsArticle, SearchQuery
from OGL.utils.news_api_utils import check_query, get_query_id, get_sentiment_score
from datetime import datetime
from typing import List

def get_articles(query: SearchQuery) -> List[NewsArticle]:
    articles = []
    for company in query.names:
        # Step 1: Search entity
        id = get_query_id(company)
        search_results = check_query(id)
        if not search_results or "result_en" not in search_results["data"]:
            continue
        if query.language == 'en':
            result_lang = "result_en"
        else:
            result_lang = "result_zh"

        for result in search_results["data"][result_lang]:
            for article_data in result.get("articles", []):
                article_info = article_data["article"]

                publication_date = article_info["published"] #datetime.strptime(article_info["published"], '%Y-%m-%d') # Reformat into datetime
                title = article_info["title"] # Direct map
                link = article_info["url"] # Direct map
                content = article_info["text"]  # Direct map
                summary = None ## TODO: Assuming we can generate it from the article content
                source = article_info["source"] # Direct map
                sentiment = get_sentiment_score(content)  ## TODO: Use a sentiment model
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
