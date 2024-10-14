from dotenv import load_dotenv, find_dotenv
from elasticsearch import Elasticsearch
import os
import warnings
from rich import print
from rich.console import Console
from rich.markdown import Markdown

warnings.filterwarnings('ignore')
load_dotenv(find_dotenv())




console = Console()
instructions = """
# Yelp search tool

## Search Types
1. **Business Name Search**: Search for businesses by a keyword in the business name.
2. **Geospatial Search**: Find businesses within a geographical bounding box based on latitude and longitude.

## Instructions
1. For searching a business use a command of the following form "business <query-phrase>"
2. For searching businesses within a geospatial bounding box use a command of the following form "geo <top_lat> <top_lan> <bottom_lat> <bottom_lan>"
"""

markdown = Markdown(instructions)
console.print(markdown)


es = Elasticsearch(
    api_key=os.environ.get("API_KEY"),
    cloud_id=os.environ.get("CLOUD_ID")
)

def search_business_by_name(index_name, business_name, top_n=10):
    search_query = {
        "query": {
            "match": {
                "name": business_name
            }
        }
    }
    response = es.search(index=index_name, body=search_query, size=top_n)
    print("\nSearch Results for Business Name:")
    for hit in response['hits']['hits']:
        print(f"Name: {hit['_source']['name']}, Score: {hit['_score']}")


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
        elif query[0] == "business": 
            if len(query)<2:
                print(f"business query passed with no name :(")
            else:
                search_business_by_name(index_name, " ".join(query[1:]).strip())
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
