"""
Final integrated code for a LangChain agent that:
  1. Takes a Twitter URL (of either a tweet or a profile) as input.
  2. Extracts tweet data using Twitter API v2 free endpoints (via tweepy.Client).
     - If the URL contains '/status/', it fetches that specific tweet.
     - Otherwise, it treats the URL as a profile URL and fetches the most recent tweet.
  3. Cleans the tweet text.
  4. Runs sentiment analysis using VADER and computes a weighted sentiment score.
  5. Returns an overall sentiment (Bullish/Bearish/Neutral) along with supporting scores.
  
Before running:
  • Replace the placeholder TWITTER_BEARER_TOKEN with your free bearer token or set it as an environment variable.
  • Set the environment variable OPENAI_API_KEY for OpenAI.
  
Required packages:
  pip install tweepy vaderSentiment langchain openai
"""

import re
import json
import os
from datetime import datetime

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Use Tweepy Client for Twitter API v2 (free endpoints)
import tweepy

# LangChain imports
from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ====================
# Twitter API v2 Setup (Free API)
# ====================
# Replace with your Twitter Bearer Token or set as environment variable TWITTER_BEARER_TOKEN
BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN", "YOUR_TWITTER_BEARER_TOKEN")
if BEARER_TOKEN == "YOUR_TWITTER_BEARER_TOKEN":
    print("Please set your TWITTER_BEARER_TOKEN as an environment variable or update the code.")

# Initialize Tweepy Client (using only free endpoints)
client = tweepy.Client(bearer_token=BEARER_TOKEN, wait_on_rate_limit=True)

# ====================
# Helper Functions
# ====================
def extract_twitter_data(url: str) -> dict:
    """
    Extract tweet data from a Twitter URL.
    If the URL contains '/status/', it treats it as a tweet URL.
    Otherwise, it assumes a profile URL and fetches the most recent tweet.
    Returns a dictionary with tweet text, engagement metrics, and (if available) user follower count.
    """
    try:
        parts = url.strip().split('/')
        if "status" in parts:
            # URL example: https://x.com/username/status/tweet_id
            username = parts[3]
            tweet_id = parts[5]
            response = client.get_tweet(tweet_id, tweet_fields=["public_metrics", "created_at", "text"], expansions=["author_id"])
            if response.errors:
                return {"error": f"{response.errors}"}
            tweet = response.data
            # Get user info from expansions
            includes = response.includes
            if includes and "users" in includes and len(includes["users"]) > 0:
                user = includes["users"][0]
                followers_count = user.public_metrics.get("followers_count", 0)
            else:
                followers_count = 0
        else:
            # Assume profile URL: e.g., https://x.com/username
            username = parts[3]
            # Use recent search to fetch the latest tweet from the user
            query = f"from:{username}"
            search_response = client.search_recent_tweets(query=query, tweet_fields=["public_metrics", "created_at", "text"], expansions=["author_id"], max_results=10)
            if not search_response.data:
                return {"error": "No tweets found for this profile."}
            tweet = search_response.data[0]
            includes = search_response.includes
            if includes and "users" in includes and len(includes["users"]) > 0:
                user = includes["users"][0]
                followers_count = user.public_metrics.get("followers_count", 0)
            else:
                followers_count = 0

        tweet_data = {
            "username": username,
            "text": tweet.text,
            "retweet_count": tweet.public_metrics.get("retweet_count", 0),
            "favorite_count": tweet.public_metrics.get("like_count", 0),
            "created_at": str(tweet.created_at),
            "followers_count": followers_count
        }
        return tweet_data

    except Exception as e:
        return {"error": f"Error fetching tweet data: {str(e)}"}

def clean_tweet(text: str) -> str:
    """
    Cleans tweet text by removing URLs, mentions, hashtags (the '#' symbol), and extra whitespace.
    """
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#", "", text)
    return re.sub(r"\s+", " ", text).strip()

def analyze_sentiment(tweet_data: dict) -> dict:
    """
    Uses VADER to analyze the sentiment of the tweet's text.
    Returns the cleaned text, raw VADER scores, an overall sentiment label,
    and a weighted score that factors in engagement (followers, likes, retweets).
    """
    if "error" in tweet_data:
        return tweet_data

    analyzer = SentimentIntensityAnalyzer()
    cleaned_text = clean_tweet(tweet_data["text"])
    scores = analyzer.polarity_scores(cleaned_text)
    compound = scores["compound"]

    # Overall sentiment label
    if compound >= 0.05:
        sentiment = "Bullish"
    elif compound <= -0.05:
        sentiment = "Bearish"
    else:
        sentiment = "Neutral"

    # Weighted score calculation (adjust formula as needed)
    weight_factor = 1 + tweet_data["followers_count"] / 10000 + (tweet_data["favorite_count"] + tweet_data["retweet_count"]) / 100
    weighted_score = compound * weight_factor

    result = {
        "cleaned_text": cleaned_text,
        "vader_scores": scores,
        "overall_sentiment": sentiment,
        "weighted_score": weighted_score
    }
    return result

# ====================
# LangChain Tool Wrappers
# ====================

def twitter_data_extractor(url: str) -> str:
    data = extract_twitter_data(url)
    return json.dumps(data)

twitter_tool = Tool(
    name="TwitterDataExtractor",
    func=twitter_data_extractor,
    description=(
        "Accepts a Twitter URL (tweet or profile) and returns a JSON string containing the tweet's text, "
        "engagement metrics (retweets, likes), creation time, and user follower count (if available)."
    )
)

def sentiment_analyzer_tool(tweet_json: str) -> str:
    tweet_data = json.loads(tweet_json)
    result = analyze_sentiment(tweet_data)
    return json.dumps(result, indent=2)

sentiment_tool = Tool(
    name="SentimentAnalyzer",
    func=sentiment_analyzer_tool,
    description=(
        "Accepts a JSON string (tweet data) and returns a JSON string with the cleaned text, "
        "VADER sentiment scores, overall sentiment (Bullish/Bearish/Neutral), and a weighted score."
    )
)

# ====================
# Initialize the LangChain Agent
# ====================

# Ensure OPENAI_API_KEY is set in your environment.
llm = OpenAI(temperature=0)
agent = initialize_agent(
    tools=[twitter_tool, sentiment_tool],
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)

# ====================
# Main Execution Block
# ====================
# if __name__ == "__main__":
#     twitter_url = input("Enter a Twitter URL: ").strip()
#     result = agent.run(twitter_url)
#     print("\nFinal Result:")
#     print(result)
