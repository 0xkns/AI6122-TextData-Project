import os
import warnings

from dotenv import find_dotenv, load_dotenv
from elasticsearch import Elasticsearch
from rich import print
from rich.console import Console
from rich.markdown import Markdown

from review_summary import review_cli

warnings.filterwarnings("ignore")
load_dotenv(find_dotenv())

console = Console()
instructions = """
# Yelp search tool for businesses and reviews

## Search Types
1. 
2. **User Review Summary**: Look at how people have written reviews with a summary for each user.

## Instructions
1. For viewing the review summary of a particular user input a valid user ID of form "user id".
2. To exit, type "exit".
"""

markdown = Markdown(instructions)
console.print(markdown)


def setup():
    try:
        es = Elasticsearch(
            api_key=os.environ.get("API_KEY"), cloud_id=os.environ.get("CLOUD_ID")
        )
        return es
    except Exception as e:
        print("Error:", e)
        raise


def review(es):
    review_summary = review_cli.ReviewSummary(es)

    while True:
        query = input("query: ").strip().split(" ")
        query[0] = query[0].lower()

        if query[0] == "exit":
            print("Exiting the search tool. Goodbye!")
            break

        if query[0] == "user":
            if len(query) < 2:
                print("No user id specified.")
                continue
            try:
                user_id = query[1]
                review_summary.generate_user_review_summary(user_id)
            except Exception as e:
                print(e)
        else:
            print(
                "Invalid search type. Please enter 'overall', 'user <id>', or 'exit'."
            )

        print("\n")


def business(es):
    pass


def main():
    es = setup()

    if True:
        review(es)
    else:
        business(es)


if __name__ == "__main__":
    main()
