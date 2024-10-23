
"""
Copyright (C) 2023 SE23-Team44
 
Licensed under the MIT License.
See the LICENSE file in the project root for the full license information.
"""

def filter(products, min_price=None, max_price=None, min_rating=None):
    """
    Filters the list of products based on price range and minimum rating.
    
    Parameters:
    - products: List of product dictionaries.
    - min_price: Minimum price to filter by.
    - max_price: Maximum price to filter by.
    - min_rating: Minimum rating to filter by.
    
    Returns:
    - A list of filtered products.
    """
    filtered_products = []
    
    for product in products:
        # Extract price and rating, ensuring we handle missing data
        try:
            price = float(product['price'].replace('$', '').replace(',', '')) if product['price'] != 'N/A' else None
        except (ValueError, KeyError):
            price = None
        
        try:
            rating = float(product['rating']) if product['rating'] != 'N/A' else None
        except (ValueError, KeyError):
            rating = None
        
        # Apply filters
        if min_price is not None and price is not None and price < min_price:
            continue
        if max_price is not None and price is not None and price > max_price:
            continue
        if min_rating is not None and rating is not None and rating < min_rating:
            continue
        
        # Add product to the filtered list if it meets all criteria
        filtered_products.append(product)
    
    return filtered_products

from flask import Flask, session, render_template, request, redirect, url_for
# from .scraper import driver, filter
from .scraper import driver
from .formatter import formatResult
import json
from .features import create_user, check_user, wishlist_add_item, read_wishlist, wishlist_remove_list, share_wishlist
from .config import Config
import re

app = Flask(__name__, template_folder=".")

app.secret_key = Config.SECRET_KEY

@app.route('/')
def landingpage():
    login = False
    if 'username' in session:
        login = True
    return render_template("./static/landing.html", login=login)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        if check_user(request.form['username'], request.form['password']):
            return redirect(url_for('login'))
        else:
            return render_template("./static/landing.html", login=False, invalid=True)
    return render_template('./static/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        session['username'] = request.form['username']
        if create_user(request.form['username'], request.form['password']):
            return redirect(url_for('login'))
        else:
            return render_template("./static/landing.html", login=False, invalid=True)
    return render_template('./static/login.html')


@app.route('/wishlist')
def wishlist():
    username = session['username']
    wishlist_name = "default"
    items = read_wishlist(username, wishlist_name).to_dict('records')
    return render_template('./static/wishlist.html', data=items)

@app.route('/share', methods=['POST'])
def share():
    username = session['username']
    wishlist_name = "default"
    email_receiver = request.form['email']
    share_wishlist(username, wishlist_name, email_receiver)
    return redirect(url_for('wishlist'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return render_template('./static/landing.html')

@app.route("/search", methods=["POST", "GET"])
def product_search(new_product="", sort=None, currency=None, num=None, min_price = None, max_price = None, min_rating = None):
    product = request.args.get("product_name")
    if product == None:
        product = new_product

    # data = driver(product, currency, num, 0, False, None, True, sort)

    data = driver(product, currency, num, False, sort)

    if min_price is not None or max_price is not None or min_rating is not None:
        data = filter(data, min_price, max_price, min_rating)

    return render_template("./static/result.html", data=data, prod=product, total_pages= len(data)//20)


@app.route("/filter", methods=["POST", "GET"])
def product_search_filtered():
    
    product = request.args.get("product_name")
    sort = request.form["sort"]
    currency = request.form["currency"]
    
    min_price = request.form["min_price"]
    max_price = request.form["max_price"]
    min_rating = request.form["min_rating"]

    try:
        min_price = float(min_price)
    except:
        min_price = None

    try:
        max_price = float(max_price)
    except:
        max_price = None

    try:
        min_rating = float(min_rating)
    except:
        min_rating = None

    if sort == "default":
        sort = None
    if currency == "usd":
        currency = None

    return product_search(product, sort, currency, None, min_price, max_price, min_rating)

@app.route("/add-wishlist-item", methods=["POST"])
def add_wishlist_item():
    username = session['username']
    item_data = request.form.to_dict()
    wishlist_name = 'default'
    wishlist_add_item(username, wishlist_name, item_data)
    return ""

@app.route("/delete-wishlist-item", methods=["POST"])
def remove_wishlist_item():
    username = session['username']
    index = int(request.form["index"]) 
    wishlist_name = 'default'
    wishlist_remove_list(username, wishlist_name, index)
    return redirect(url_for('wishlist'))

if __name__ == '__main__':
    app.run(debug=True)
