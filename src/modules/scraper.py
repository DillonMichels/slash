import requests
from bs4 import BeautifulSoup
import random
import time
import re  # Regular expression module for price extraction
from .formatter import formatResult, formatSearchQuery


def random_delay():
    """Adds a random delay between 1 to 5 seconds to avoid detection by the target website."""
    time.sleep(random.uniform(1, 5))


def get_proxies():
    """Retrieves a list of proxies from ProxyScrape and filters out invalid proxies."""
    proxy_url = 'https://www.proxyscrape.com/free-proxy-list'
    response = requests.get(proxy_url)
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve proxies. Status code: {response.status_code}")

    proxies = response.text.splitlines()
    
    # Filter out invalid proxies that contain spaces or are improperly formatted
    valid_proxies = [proxy for proxy in proxies if " " not in proxy]
    
    return valid_proxies


def httpsGetWithProxy(URL, use_proxy=False):
    """Sends an HTTP GET request using a random proxy or direct connection if no proxy is used."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'DNT': '1',  # Do Not Track Request Header
        'Cache-Control': 'no-cache'
    }

    proxies = get_proxies() if use_proxy else []
    proxy_dict = None
    if use_proxy and proxies:
        random_proxy = random.choice(proxies)
        proxy_dict = {
            'http': f"http://{random_proxy}",
            'https': f"http://{random_proxy}"
        }

    random_delay()

    try:
        response = requests.get(URL, headers=headers, proxies=proxy_dict, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve page. Status code: {response.status_code}")
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Request failed with proxy: {e}")
        return None


def searchAmazon(query, df_flag=False, currency="USD", use_proxy=False):
    """Scrapes Amazon for products matching the query."""
    query = formatSearchQuery(query)
    URL = f"https://www.amazon.com/s?k={query}"

    # Send request and parse the page
    page = httpsGetWithProxy(URL, use_proxy=use_proxy)
    if page is None:
        return []

    # Extract product results from the page
    results = page.findAll("div", {"data-component-type": "s-search-result"})

    # Initialize product list
    products = []

    # Iterate over search results and extract relevant information
    for res in results:
        titles = [title.get_text().strip() for title in res.select("h2 a span")]
        prices = [price.get_text().strip() for price in res.select("span.a-price span")]
        links = [link["href"] for link in res.select("h2 a.a-link-normal")]
        ratings = [rating.get_text().strip() for rating in res.select("span.a-icon-alt")]
        num_ratings = [num.get_text().strip() for num in res.select("span.a-size-base")]
        trending = [trend.get_text().strip() for trend in res.select("span.a-badge-text")]
        img_links = [img['src'] for img in res.select("img.s-image")]

        # Print raw scraped data for each product for debugging
        print(f"Title: {titles}, Price: {prices}, Link: {links}, Rating: {ratings}")

        # Format the result into a JSON serializable dictionary
        product = formatResult(
            "amazon", titles, prices, links, ratings, num_ratings, trending, df_flag, currency, img_links
        )
        
        products.append(product)

    return products


# Updated Walmart scraping logic
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

def search_walmart(query):
    query = query.replace(" ", "+")
    url = f"https://www.walmart.com/search/?query={query}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/',
        'DNT': '1',  # Do Not Track Request Header 
        'Connection': 'keep-alive'
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Failed to retrieve page")
        return []

    soup = BeautifulSoup(response.text, 'lxml')

    # Walmart products are generally loaded dynamically, but let's attempt basic scraping
    products = []

    for product in soup.find_all('div', {'class': 'search-result-product-title gridview'}):
        try:
            title = product.find('a').text.strip()
            link = 'https://www.walmart.com' + product.find('a')['href']
            price = product.find('span', {'class': 'price-characteristic'}).text
            products.append({
                'title': title,
                'price': price,
                'link': link
            })
        except AttributeError:
            continue

    return products

def driver(product, currency, num, df_flag, sort):
    """
    Driver function that coordinates scraping both Amazon and Walmart.
    
    Parameters:
    - product: The product name to search.
    - currency: Currency to display.
    - num: Number of products to return.
    - df_flag: Dataframe flag for additional processing (optional).
    - sort: Whether to sort by price.
    
    Returns a list of products from both Amazon and Walmart.
    """
    print(f"Scraping products for query: {product} from Amazon and Walmart")

    # Scrape Amazon
    products_amazon = searchAmazon(product, df_flag, currency, use_proxy=True)
    print(f"Amazon results: {len(products_amazon)} products scraped.")

    # Scrape Walmart
    products_walmart = search_walmart(product, df_flag, currency, use_proxy=True)
    print(f"Walmart results: {len(products_walmart)} products scraped.")

    # Combine Amazon and Walmart products
    combined_products = products_amazon + products_walmart

    # Limit the number of products returned if specified
    if num and len(combined_products) > num:
        combined_products = combined_products[:num]

    # Sort the results if sorting is requested
    if sort:
        try:
            combined_products.sort(key=lambda x: float(x['price'].replace('$', '').replace(',', '')))
        except ValueError:
            print("Error in sorting: some products may not have valid prices.")

    # Return the combined list of products
    return combined_products

