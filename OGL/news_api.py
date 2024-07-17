from utils.news_api_template import NewsArticle, SearchQuery
from utils.news_api_utils import check_query, get_query_id, get_sentiment_score, get_summary, save_articles_to_json
from datetime import datetime
from typing import List

import warnings

def get_articles(query: SearchQuery) -> List[NewsArticle]: #TODO: If many companies in query, fetch results concurrently
    articles = []
    for company in query.names:
        # Step 1: Search entity to get ID of company -> This will take a while - Implement ping every 1 minute
        id = get_query_id(company)
        print(f"Entity {company} query id is: {id}")
        # Step 2: Get articles associated with entity ID
        search_results = check_query(id)
        if not search_results or 'data' not in search_results.keys():
            print("Unable to fetch results for Entity {company}")
            continue
        else:
            print(f"Entity {company} search results contain: {search_results['data'].keys}")
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
                        keywords = []
                        categories = []
                        image = None

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

#For testing
if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    names = ["New World Development Co Ltd"]
    query = SearchQuery(names=names, language='en', since=datetime(2024, 1, 1))
    articles = get_articles(query)
    save_articles_to_json(articles, f"{'_'.join(names)}_articles.json")