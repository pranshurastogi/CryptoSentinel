import requests

def get_details(token_address, platform="base"):
    """
    Given a token contract address, this function returns a dictionary of selected details
    that may be useful for an AI investment agent, including:
    
      - Basic identifiers: id, symbol, name, description (in English), and contract address.
      - Platforms and decimals (from detail_platforms for the specified platform).
      - Categories and links.
      - Image information.
      - Sentiment data (votes up/down) and watchlist portfolio users.
      - Market ranking and market data such as current price, market cap, total, max and circulating supply,
        as well as 24h high/low and price change percentage.
      - Additional market details: total_value_locked, mcap_to_tvl_ratio.
      - ATH and ATL in USD along with their change percentages.
      - Trading details: a list of tickers with each ticker’s market name, last price (in USD), volume (in USD),
        trade URL, bid/ask spread percentage, timestamp, and trust score.
      - Community data.
    
    Parameters:
      token_address (str): The token contract address (e.g. for an ERC-20 token).
      platform (str): The network identifier for CoinGecko (default "base").
    
    Returns:
      dict: A dictionary containing the selected token details.
    """
    print('I am inside get_details')

    cg_url = f"https://api.coingecko.com/api/v3/coins/{platform}/contract/{token_address}"
    cg_response = requests.get(cg_url)
    if cg_response.status_code != 200:
        raise Exception(f"CoinGecko API error: {cg_response.status_code} - {cg_response.text}")
    
    token_data = cg_response.json()
    
    md = token_data.get("market_data", {})
    details = {
        "id": token_data.get("id"),
        "symbol": token_data.get("symbol"),
        "name": token_data.get("name"),
        "description": token_data.get("description", {}).get("en"),
        "contract_address": token_data.get("contract_address"),
        "platforms": token_data.get("platforms"),
        # Extract decimals from detail_platforms for the chosen platform (if available)
        "decimals": token_data.get("detail_platforms", {}).get(platform, {}).get("decimal_place"),
        "categories": token_data.get("categories"),
        "links": token_data.get("links"),
        "image": token_data.get("image"),
        "sentiment_votes_up_percentage": token_data.get("sentiment_votes_up_percentage"),
        "sentiment_votes_down_percentage": token_data.get("sentiment_votes_down_percentage"),
        "watchlist_portfolio_users": token_data.get("watchlist_portfolio_users"),
        "market_cap_rank": token_data.get("market_cap_rank"),
        # Market data details:
        "current_price_usd": md.get("current_price", {}).get("usd"),
        "market_cap_usd": md.get("market_cap", {}).get("usd"),
        "total_supply": md.get("total_supply"),
        "max_supply": md.get("max_supply"),
        "circulating_supply": md.get("circulating_supply"),
        "24h_high_usd": md.get("high_24h", {}).get("usd"),
        "24h_low_usd": md.get("low_24h", {}).get("usd"),
        "price_change_percentage_24h": md.get("price_change_percentage_24h"),
        # Additional market data:
        "total_value_locked": md.get("total_value_locked"),
        "mcap_to_tvl_ratio": md.get("mcap_to_tvl_ratio"),
        "ath_usd": md.get("ath", {}).get("usd"),
        "ath_change_percentage_usd": md.get("ath_change_percentage", {}).get("usd"),
        "atl_usd": md.get("atl", {}).get("usd"),
        "atl_change_percentage_usd": md.get("atl_change_percentage", {}).get("usd"),
        # Community data:
        "community_data": token_data.get("community_data"),
        "last_updated": token_data.get("last_updated")
    }
    
    # Extract trading details (tickers) in USD that may be useful for investment decision-making.
    tickers = token_data.get("tickers", [])
    trading_details = []
    for ticker in tickers:
        td = {
            "market_name": ticker.get("market", {}).get("name"),
            "last_price_usd": ticker.get("converted_last", {}).get("usd"),
            "volume_usd": ticker.get("converted_volume", {}).get("usd"),
            "trade_url": ticker.get("trade_url"),
            "bid_ask_spread_percentage": ticker.get("bid_ask_spread_percentage"),
            "timestamp": ticker.get("timestamp"),
            "trust_score": ticker.get("trust_score")
        }
        trading_details.append(td)
    details["trading_details"] = trading_details
    print('I am inside get_details',details["trading_details"])

    
    return details

# Example usage:
# if __name__ == "__main__":
#     # Replace with your token contract address (for example, the "aixbt" token on Base)
#     token_addr = "0x4f9fd6be4a90f2620860d680c0d4d5fb53d1a825"
#     token_details = get_details(token_addr)
#     print(token_details)
