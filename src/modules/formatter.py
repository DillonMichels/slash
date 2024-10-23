"""
The formatter module focuses on processing raw text and returning it in 
the required format. 
"""

from datetime import datetime
import requests
import re
from ast import literal_eval

# Exchange rates API and global exchange rate dictionary
CURRENCY_URL = "https://api.exchangerate-api.com/v4/latest/usd"
EXCHANGES = literal_eval(requests.get(CURRENCY_URL).text)

def formatResult(
    website, titles, prices, links, ratings, num_ratings, trending, df_flag, currency, img_link=None
):
    """
    Format the result for Walmart products and other websites.
    Extract and format the required fields from the scraped data.
    """
    # Initialize variables
    title, price, link, rating, num_rating, converted_cur, trending_stmt = (
        "N/A",
        "N/A",
        "N/A",
        "N/A",
        "N/A",
        "N/A",
        "N/A",
    )

    # Handle Walmart-specific title processing
    if website == "walmart":
        title = titles[0] if titles else "N/A"

    # Process price
    if prices:
        price = prices[0]  # Use the first available price
        price = price.replace(" ", "").replace(",", "")  # Clean the price string
        price_match = re.search(r"\d+\.\d+", price)  # Match the price format
        if price_match:
            price = f"${price_match.group()}"
        else:
            price = "N/A"
    
    # Process product link
    if links:
        link = links[0]
        link = f"www.{website}.com{link}" if not link.startswith("http") else link

    # Handle ratings and number of ratings
    rating = ratings[0] if ratings else "N/A"
    num_rating = num_ratings[0] if num_ratings else "N/A"

    # Handle trending information (if applicable)
    trending_stmt = trending[0] if trending else "N/A"

    # Handle image link
    img_link = img_link[0] if img_link and isinstance(img_link, list) else "https://example.com/default_image.jpg"

    # Convert the price into the desired currency if applicable
    if currency:
        converted_cur = getCurrency(currency, price)

    # Construct the final product dictionary
    product = {
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "title": title,
        "price": price,
        "img_link": img_link,
        "link": link,
        "website": website,
        "rating": rating,
        "no_of_ratings": num_rating,
        "trending": trending_stmt,
        "converted_price": converted_cur,
    }

    return product


def sortList(arr, sortBy, reverse):
    """
    Sorts the products list based on the sortBy flag. Currently, it supports sorting by price and rating.
    Parameters: arr- List of product dictionaries, sortBy- "pr" for price, "ra" for rating
    Returns: Sorted list of the products.
    """
    if sortBy == "pr":
        return sorted(arr, key=lambda x: getNumbers(x['price']), reverse=reverse)
    elif sortBy == "ra":
        return sorted(arr, key=lambda x: float(x['rating']) if x['rating'] else 0, reverse=reverse)
    return arr


def formatSearchQuery(query):
    """Formats the search string for URL parameters."""
    return query.replace(" ", "+")


def formatTitle(title):
    """Formats titles extracted from the scraped HTML code."""
    return title[:40] + "..." if len(title) > 40 else title


def getNumbers(st):
    """Extracts float values from a price string, such as '$10.99'."""
    st = str(st)
    ans = "".join(ch for ch in st if ch.isdigit() or ch == ".")
    try:
        return float(ans)
    except ValueError:
        return 0


def getCurrency(currency, price):
    """
    Converts the price listed in USD to the user-specified currency.
    Supports INR, EURO, AUD, YUAN, YEN, and POUND.
    """
    try:
        amount = float(re.search(r"[0-9\.]+", price).group()) if price else 0.0
        conversion_rate = EXCHANGES["rates"].get(currency.upper(), 1)
        converted_cur = conversion_rate * amount
        return f"{currency.upper()} {round(converted_cur, 2)}"
    except (AttributeError, KeyError, ValueError) as e:
        print(f"Error in currency conversion: {e}")
        return None
