from utils.news_api_template import NewsArticle, SearchQuery
from utils.news_api_utils import convert_to_datetime, check_query, get_query_id, get_sentiment_score, get_summary, get_bloomberg_article, get_image_from_link, save_articles_to_json
from datetime import datetime
from typing import List
import concurrent.futures
import warnings

def fetch_articles_for_entity(entity: str, query: SearchQuery) -> List[NewsArticle]:
    articles = []
    
    # Step 1: Search entity to get ID
    if entity in query.companies:
        entity_type = "company"

    elif entity in query.names:
        entity_type = "individual"
    else:
        print(f"Unexpected error with {entity} - No articles will be returned")
        return []
    id = get_query_id(entity, entity_type)
    print(f"{entity} of type {entity_type} query id is: {id}")

    # Step 2: Get articles associated with entity ID
    search_results = check_query(id)
    if not search_results or 'data' not in search_results.keys():
        print(f"Unable to fetch results for Entity {entity}")
        return articles
    else:
        print(f"Entity {entity} search results contain: {search_results['data'].keys()}")
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
        futures = {executor.submit(fetch_articles_for_entity, entity, query): entity for entity in query.names + query.companies}

        for future in concurrent.futures.as_completed(futures):
            entity = futures[future]
            try:
                result_articles = future.result()
                articles.extend(result_articles)
            except Exception as e:
                print(f"Error fetching articles for {entity}: {e}")

    return articles

# For testing
if __name__ == "__main__":
    '''
    {"names": ["Abdulla Ghurair"], 
                  "companies": ["Mashreqbank", "Mashreq Bank", "Abdulla Al Ghurair Foundation", "Mashreq Group", "Abdulla Al Ghurair Foundation (agf)", "Abdullah Al Ghurair Education Foundation", "Abdulla Al Ghurair Foundation For Education", "Al Ghurair Investment"], 
                  "language": "en", 
                  "since": "None"}
    { "names": ["马云", "馬雲"], "companies": ["阿里巴巴（中国）", "网络技术有限公司"], "language": "zh-cn", "since": "None"}
{ "names": ["黄峥", "Colin Huang", "黃崢"], "companies": ["拼多多"], "language": "zh-cn", "since": "None"}
    
    '''
    test_query = { "names": ["黄峥", "黃崢"], "companies": [], "language": "zh-cn", "since": "None"}
    query = SearchQuery(names=test_query['names'],
                        companies=test_query['companies'],
                        language=test_query['language'],
                        since=convert_to_datetime(test_query['since']))
    articles = get_articles(query)
    print("Articles collated, saving to json")
    save_articles_to_json(articles, f"OGL/examples_articles/{'_'.join(test_query['names'])}_articles.json")
