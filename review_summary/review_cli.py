from rich import print


class ReviewSummary:
    def __init__(self, es):
        self.es = es

    def overall_summary(self, index_name, business_name, top_n=10):
        search_query = {"query": {"term": {"name": business_name}}}

        response = self.es.search(index=index_name, body=search_query, size=top_n)
        print("\nSearch Results for Business Name:")
        for hit in response["hits"]["hits"]:
            print(f"Name: {hit['_source']['name']}, Score: {hit['_score']}")

    def user_summary(self, index_name, user_id):
        query = {
            "query": {"term": {"user_id": user_id}},
            "aggs": {
                "review_count": {"value_count": {"field": "user_id"}},
                "unique_businesses": {"terms": {"field": "business_id", "size": 5000}},
            },
            "_source": ["business_id"],
            "size": 0,
        }

        try:
            response = self.es.search(index=index_name, body=query)

            review_count = response["aggregations"]["review_count"]["value"]
            business_ids = [
                bucket["key"]
                for bucket in response["aggregations"]["unique_businesses"]["buckets"]
            ]

        except Exception as e:
            print(f"Error analyzing user reviews: {e}")
            raise

        print(f"\nSummary of User {user_id}:")
        print(f"1. Number of Reviews: {review_count}")
        print(f"2. Business Reviewed: {business_ids[:10]}, Business Bounding Box: ")
        print("3. Top ten Frequent words: , Top ten Frequent Phrases: ")
        print("4. Top three Representative Sentences: ")


def test():
    index_name = "review_index"
    review_summary = ReviewSummary()

    while True:
        query = input("query: ").strip().split(" ")
        query[0] = query[0].lower()

        if query[0] == "exit":
            print("Exiting the search tool. Goodbye!")
            break

        if query[0] == "overall":
            review_summary.overall_summary(index_name, " ".join(query[1:]).strip())
        elif query[0] == "user":
            if len(query) < 2:
                print("No user id specified.")
                continue
            try:
                user_id = query[1]
                review_summary.user_summary(index_name, user_id)
            except Exception as e:
                print(e)
        else:
            print(
                "Invalid search type. Please enter 'overall', 'user <id>', or 'exit'."
            )

        print("\n")


if __name__ == "__main__":
    test()
