import string
from collections import Counter

import nltk
import numpy as np
import pandas as pd
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from rich import print

# Setup NLTK for text processing
nltk.download("punkt")
nltk.download("stopwords")

# Load stopwords and define punctuation to remove
stop_words = set(stopwords.words("english"))
punctuation = set(string.punctuation)


class ReviewSummary:
    def __init__(self, es):
        self.es = es

    def get_user_reviews_from_es(self, user_id, index_name="review_index"):
        query = {
            "query": {"term": {"user_id": user_id}},
            "aggs": {
                "review_count": {"value_count": {"field": "user_id"}},
                "unique_businesses": {"terms": {"field": "business_id", "size": 5000}},
            },
            "_source": ["business_id", "text"],
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

        # Extract hits (reviews)
        reviews = [hit["_source"] for hit in response["hits"]["hits"]]

        # Convert to DataFrame
        if reviews:
            return pd.DataFrame(reviews), review_count, business_ids
        else:
            return pd.DataFrame(), None, None

    def bounding_box(self, X, Y, r=10, R=6.4):
        C = 2 * np.pi * R

        dY = r * C / 360
        dX = dY * np.cos(np.radians(Y))

        Xmin, Ymin = X - dX, Y - dY
        Xmax, Ymax = X + dX, Y + dY
        return (Xmin, Ymin, Xmax, Ymax)

    def get_bounding_box(self, business_ids, index_name="business_data"):

        response = self.es.search(
            index=index_name,
            query={
                "bool": {
                    "should": [
                        {"match": {"business_id": value}} for value in business_ids
                    ]
                }
            },
            size=10000,
        )

        return response

    # 3. Top 10 most frequent words (excluding stopwords)
    def get_top_words(self, user_reviews, top_n=10):
        all_reviews = " ".join(user_reviews["text"])
        tokens = word_tokenize(all_reviews.lower())
        # Filter out stopwords and punctuation
        tokens = [word for word in tokens if word.isalpha() and word not in stop_words]
        word_freq = Counter(tokens).most_common(top_n)
        return word_freq

    # 4. Top 10 most frequent phrases (bi-grams)
    def get_top_phrases(self, user_reviews, top_n=10):
        all_reviews = " ".join(user_reviews["text"])
        tokens = word_tokenize(all_reviews.lower())
        # Filter out stopwords and punctuation
        tokens = [word for word in tokens if word.isalpha() and word not in stop_words]
        bi_grams = list(nltk.bigrams(tokens))
        phrase_freq = Counter(bi_grams).most_common(top_n)
        return phrase_freq

    # 5. Three most representative sentences
    def get_representative_sentences(self, user_reviews, top_n=3):
        all_reviews = " ".join(user_reviews["text"])
        sentences = sent_tokenize(all_reviews)

        # Simple approach: pick the three longest sentences (could be based on sentiment, frequency, etc.)
        sorted_sentences = sorted(sentences, key=len, reverse=True)[:top_n]
        return sorted_sentences

    # Main function to generate user review summary
    def generate_user_review_summary(self, user_id):
        # Get user-specific reviews
        user_reviews, review_count, business_ids = self.get_user_reviews_from_es(
            user_id
        )

        if user_reviews.empty:
            print(f"No reviews found for user ID: {user_id}")
            return

        # 1. Number of reviews contributed
        business_ids_10 = " ".join(business_ids[:10])
        print(
            f"\nThe user, {user_id}, has contributed {review_count} reviews. 10 businesses reviewed are, {business_ids_10}"
        )

        # 2. Bounding Box:
        print(f"\nThe Bounding boxes of Business {business_ids_10} are: ")
        bounding_boxes = self.get_bounding_box(business_ids)
        for hit in bounding_boxes["hits"]["hits"][:10]:
            print(
                self.bounding_box(
                    hit["_source"]["longitude"], hit["_source"]["latitude"]
                )
            )

        # 3. Top-10 most frequent words
        top_words = self.get_top_words(user_reviews)
        print("\nTop 10 most frequent words:")
        for word, freq in top_words:
            print(f"Word: {word}, Frequency: {freq}")

        # 4. Top-10 most frequent phrases
        top_phrases = self.get_top_phrases(user_reviews)
        print("\nTop 10 most frequent phrases (bi-grams):")
        for phrase, freq in top_phrases:
            print(f"Phrase: {' '.join(phrase)}, Frequency: {freq}")

        # 5. Three most representative sentences
        representative_sentences = self.get_representative_sentences(user_reviews)
        print("\nThree most representative sentences:")
        for i, sentence in enumerate(representative_sentences, 1):
            print(f"{i}: {sentence}")
            print()


def test():
    index_name = "review_index"
    review_summary = ReviewSummary()

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
                review_summary.generate_user_review_summary(index_name, user_id)
            except Exception as e:
                print(e)
        else:
            print(
                "Invalid search type. Please enter 'overall', 'user <id>', or 'exit'."
            )

        print("\n")


if __name__ == "__main__":
    test()
