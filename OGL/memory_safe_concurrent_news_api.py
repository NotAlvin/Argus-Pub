from datetime import datetime
import time
import concurrent.futures
from typing import List, Dict
import json
import random
import logging
import os

from utils.news_api_template import NewsArticle, SearchQuery
from utils.news_api_utils import (
    convert_to_datetime, check_query, get_query_id, get_sentiment_score,
    get_summary, get_bloomberg_article, get_image_from_link, save_articles_to_json
)

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
    print(f"Searching for {entity} of type {entity_type}")
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
                summary = article_info.get("summary", get_summary(content, result_lang[-2:])) # en or zh
                source = article_info["source"]
                sentiment = get_sentiment_score(content)
                image = get_image_from_link(link)

                if title == "Bloomberg - Are you a robot?":
                    title, content = get_bloomberg_article(link)
                    summary = get_summary(content, result_lang[-2:])
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
                    image=image
                ))

        return articles

def fetch_articles_with_delay(entity: str, query: SearchQuery, delay: float) -> List[NewsArticle]:
    time.sleep(delay)  # Add delay before making the API call
    return fetch_articles_for_entity(entity, query)

def get_articles(query: SearchQuery, delay: float = 0.5) -> None:
    entities = query.names + query.companies
    articles_dir = "./examples_articles/"
    if not os.path.exists(articles_dir):
        os.makedirs(articles_dir)

    # Setup logging
    logging.basicConfig(filename='error_log.log', level=logging.ERROR)

    def fetch_and_write_articles(entity):
        try:
            result_articles = fetch_articles_with_delay(entity, query, delay)
            # Remove duplicates within the fetched articles
            unique_articles = {article.title: article for article in result_articles}.values()
            # Write articles to JSON file in batches
            batch_size = 5
            for i in range(0, len(unique_articles), batch_size):
                batch = list(unique_articles)[i:i + batch_size]
                file_path = f"{articles_dir}{entity}_articles_batch_{i // batch_size + 1}.json"
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump([article.__dict__ for article in batch], f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Error fetching articles for {entity}: {e}")

    # Use ThreadPoolExecutor for concurrent API calls
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(fetch_and_write_articles, entity) for entity in entities]
        for future in concurrent.futures.as_completed(futures):
            future.result()  # Propagate exceptions if any

    logging.info("All articles have been fetched and written to JSON files.")

def read_all_articles(query: SearchQuery) -> Dict[str, List[NewsArticle]]:
    entities = query.names + query.companies
    articles_by_entity = {}
    articles_dir = "./examples_articles/"

    for entity in entities:
        for file_name in os.listdir(articles_dir):
            if file_name.startswith(entity) and file_name.endswith('.json'):
                with open(os.path.join(articles_dir, file_name), 'r', encoding='utf-8') as f:
                    batch_articles = json.load(f)
                    if entity not in articles_by_entity:
                        articles_by_entity[entity] = []
                    articles_by_entity[entity].extend([NewsArticle(**article) for article in batch_articles])

    return articles_by_entity

if __name__ == "__main__":
    json_file_path = './utils/test_cases.json'

    with open(json_file_path, 'r') as file:
        data = [json.loads(line) for line in file]

    test_query = random.choice(data)
    query = SearchQuery(names=test_query['names'],
                        companies=test_query['companies'],
                        language=test_query['language'],
                        since=convert_to_datetime(test_query['since']))

    # Fetch articles with delay and save them to JSON files in batches
    get_articles(query, delay=0.5)  # Adjust delay as needed

    # Read all articles back into memory for the specific query entities
    articles_by_entity = read_all_articles(query)

    # Saving all collated articles to a single JSON file (if needed)
    combined_file_name = '_'.join(test_query['names'] + test_query['companies']) + "_articles_combined.json"
    combined_articles = [article for articles in articles_by_entity.values() for article in articles]
    try:
        with open(f"./examples_articles/{combined_file_name}", 'w', encoding='utf-8') as f:
            json.dump([article.__dict__ for article in combined_articles], f, ensure_ascii=False, indent=4)
    except:
        try:
            fallback_file_name = '_'.join(test_query['names']) + "_articles_combined.json"
            with open(f"./examples_articles/{fallback_file_name}", 'w', encoding='utf-8') as f:
                json.dump([article.__dict__ for article in combined_articles], f, ensure_ascii=False, indent=4)
        except:
            with open(f"./examples_articles/last_searched_articles_combined.json", 'w', encoding='utf-8') as f:
                json.dump([article.__dict__ for article in combined_articles], f, ensure_ascii=False, indent=4)
