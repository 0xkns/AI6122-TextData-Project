from dotenv import load_dotenv, find_dotenv
from elasticsearch import Elasticsearch
import os
import warnings
from rich import print
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from nltk.corpus import wordnet as wn

warnings.filterwarnings('ignore')
load_dotenv(find_dotenv())

business_index = "business_data"
review_index = "business_review_data"



console = Console()
instructions = """
# Yelp search tool

## Search Types
1. **Business Name Search**: Search for businesses by a keyword in the business name.
2. **Geospatial Search**: Find businesses within a geographical bounding box based on latitude and longitude.

## Instructions
1. For searching a business or a review you can just key in the phrase"
2. For searching businesses within a geospatial bounding box use a command of the following form "geo <top_lat> <top_lan> <bottom_lat> <bottom_lan>"
"""

markdown = Markdown(instructions)
console.print(markdown)


es = Elasticsearch(
    api_key=os.environ.get("API_KEY"),
    cloud_id=os.environ.get("CLOUD_ID")
)

def get_alternate_phrase(phrase):
    alternate_phrase = ""
    for word in phrase.strip().split():
        alternate_phrase += wn.synsets(word)[1].lemmas()[0].name() + " "
    return alternate_phrase.strip()

def search_reviews(phrase, top_n=10):
    all_phrases = [phrase, get_alternate_phrase(phrase)]
    search_query = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"text": _phrase}} for _phrase in all_phrases
                ]
            }
        }
    }
    response = es.search(index=review_index, body=search_query, size=top_n)
    return response


def search_business(phrase, top_n=10):
    search_query = {
        "query": {
            "match": {
                "name": phrase
            }
        }
    }
    response = es.search(index=business_index, body=search_query, size=top_n)
    return response



def search(phrase):
    if len(phrase.strip().split()) == 1:
        response = search_business(phrase)
        console.print(Markdown("### Top business results\n"))
        
        # Use a table for better formatting
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Business Name", width=30)
        table.add_column("Address", width=50)
        
        for hit in response['hits']['hits']:
            table.add_row(hit['_source']['name'], hit['_source']['address'])
        console.print(table)
    else:
        reviews = search_reviews(phrase)
        business = search_business(phrase)
        
        reviews = sorted([(hit['_source'], hit['_score']) for hit in reviews['hits']['hits']], key=lambda l: -l[1])[:5]
        business = sorted([(hit['_source'], hit['_score']) for hit in business['hits']['hits']], key=lambda l: -l[1])[:5]
        
        console.print(Markdown("### Top business results\n"))
        
        # Business results table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Business Name", width=30)
        table.add_column("Address", width=50)
        for source, _ in business:
            table.add_row(source['name'], source['address'])
        console.print(table)
        
        console.print(Markdown("\n### Top review results\n"))
        
        # Review results table
        review_table = Table(show_header=True, header_style="bold green")
        review_table.add_column("Business Name", width=30)
        review_table.add_column("Review", width=70)
        for source, _ in reviews:
            business_name = es.get(index=business_index, id=source['business_id'])['_source']['name']
            review_table.add_row(business_name, source['text'])
        console.print(review_table)



def search_business_by_location(index_name, top_left, bottom_right, top_n=10):
    search_query = {
        "query": {
            "geo_bounding_box": {
                "location": {
                    "top_left": top_left,
                    "bottom_right": bottom_right
                }
            }
        }
    }
    response = es.search(index=index_name, body=search_query, size=top_n)
    print("\nSearch Results for Location:")
    for hit in response['hits']['hits']:
        print(f"Name: {hit['_source']['name']}, Location: {hit['_source']['location']}")


def main():
    index_name = "business_data"

    print("Yelp search tool for businesses and reviews")
    print(f"Instructions")
    print("Type 'exit' to quit at any time.\n")

    while True:
        query = input(f"query: ").strip().lower()
        query = query.split(" ")
        if query[0] == "exit":
            print("Exiting the search tool. Goodbye!")
            break
        elif query[0] != "geo": 
            search(" ".join(query).strip())
        elif query[0] == "geo":
            if len(query)<5:
                print(f"geo query passed with few params :(")
                continue
            
            for q in query[1:]:
                try:
                    _ = float(q)
                except:
                    print(f"lat lon values are not real valued numbers :(")
                    continue
            
            query[1:] = [float(q) for q in query[1:]]
            try:
                top_left = {"lat": query[1], "lon": query[2]}
                bottom_right = {"lat": query[3], "lon": query[4]}
                search_business_by_location(index_name, top_left, bottom_right)
            except Exception as e: 
                print(e)
        else:
            print("Invalid search type. Please enter 'name', 'geo', or 'exit'.")

        print("\n")  


if __name__ == "__main__":
    main()
