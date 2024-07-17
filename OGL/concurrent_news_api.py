from utils.news_api_template import NewsArticle, SearchQuery
from utils.news_api_utils import check_query, get_query_id, get_sentiment_score, get_summary, get_bloomberg_article, get_image_from_link, save_articles_to_json
from datetime import datetime
from typing import List
import concurrent.futures
import warnings

def fetch_articles_for_company(company: str, query: SearchQuery) -> List[NewsArticle]:
    articles = []
    
    # Step 1: Search entity to get ID of company
    id = get_query_id(company)
    print(f"Entity {company} query id is: {id}")

    # Step 2: Get articles associated with entity ID
    search_results = check_query(id)
    if not search_results or 'data' not in search_results.keys():
        print(f"Unable to fetch results for Entity {company}")
        return articles
    else:
        print(f"Entity {company} search results contain: {search_results['data'].keys()}")
        result_lang = "result_en" if query.language == 'en' else "result_zh"

        # Step 3: Process articles
        for result in search_results["data"][result_lang]:
            for article_data in result.get("articles", []):
                article_info = article_data["article"]
                publication_date = datetime.strptime(article_info["published"], '%Y-%m-%d') if article_info["published"] else None
                
                if query.since and publication_date and publication_date <= query.since:
                    continue
                
                title = article_info["title"]
                link = article_info["url"]
                content = article_info["text"]
                summary = article_info.get("summary", get_summary(content))
                source = article_info["source"]
                sentiment = get_sentiment_score(content)
                image = get_image_from_link(link)

                if title == "Bloomberg - Are you a robot?":
                    title, content = get_bloomberg_article(link)
                    summary = get_summary(content)
                    sentiment = get_sentiment_score(content)

                articles.append(NewsArticle(
                    publication_date=publication_date,
                    title=title,
                    link=link,
                    content=content,
                    summary=summary,
                    source=source,
                    sentiment=sentiment,
                    keywords=[],  # TODO: Check with LEDR
                    categories=[],  # TODO: Check with LEDR
                    image=image  # TODO: Extract this from somewhere
                ))

        return articles

def get_articles(query: SearchQuery) -> List[NewsArticle]:
    articles = []
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(fetch_articles_for_company, company, query): company for company in query.names}

        for future in concurrent.futures.as_completed(futures):
            company = futures[future]
            try:
                result_articles = future.result()
                articles.extend(result_articles)
            except Exception as e:
                print(f"Error fetching articles for {company}: {e}")

    return articles

# For testing
if __name__ == "__main__":
    names = ["New World Development Co Ltd"]
    query = SearchQuery(names=names, language='en', since=datetime(2024, 1, 1))
    articles = get_articles(query)
    save_articles_to_json(articles, f"OGL/examples_articles/{'_'.join(names)}_articles.json")
