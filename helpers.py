import os
import csv
import datetime
import pytz
import requests
import subprocess
import urllib
import uuid
import inflect
import json
from cs50 import SQL
from flask import redirect, render_template, session
from functools import wraps

db = SQL("sqlite:///branded.db")

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.
        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def lookup_nutritional_info(query, api_key):
    """Look up food's nutrional value."""
    # USDA FDC API
    base_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "query": query,
        "api_key": api_key
    }
    # Query API
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()  # Parses JSON data into a dictionary

        if "foods" in data and len(data["foods"]) > 0:
            food = data["foods"][0]
            nutrient_data = food.get("foodNutrients", [])
            nutritional_info = {
                "name": food.get("description", ""),
                "fdc_id": food.get("fdcId", ""),
                "serving_size": food.get("servingSize", ""),
                "nutrients": [
                    {
                        "name": nutrient["nutrientName"],
                        "value": nutrient["value"],
                        "unit": nutrient["unitName"]
                    }
                    for nutrient in nutrient_data
                ]
            }
            return nutritional_info
        else:
            return None
    except (requests.RequestException, ValueError, KeyError):
        return None


def search_food(query, api_key, page, page_size):
    base_url = "https://api.nal.usda.gov/fdc/v1/"
    data_types = ["Survey (FNDDS)", "SR Legacy", "Foundation"]

    response = requests.get(
        base_url + f'foods/search?query={query}&api_key={api_key}&pageNumber={page}&pageSize={page_size}&dataType={",".join(data_types)}'
    )
    response.raise_for_status()  # Raise an exception if there's an HTTP error

    data = response.json()
    search_results = []
    total_hits = data.get('totalHits', 0)

    if 'foods' in data:
        for food in data['foods']:
            food_name = food['description']
            fdc_id = food['fdcId']
            search_results.append({
                "food_name": food_name,
                "fdc_id": fdc_id,
            })

    return search_results, total_hits



def get_nutritional_info(fdc_ids, api_key):
    base_url = "https://api.nal.usda.gov/fdc/v1/"

    # Convert the list of fdc_ids to a comma-separated string
    fdc_ids_str = ",".join(map(str, fdc_ids))

    # Specify the nutrient numbers you want to retrieve (e.g., 203 for Protein, 204 for Total lipid (fat), etc.)
    nutrient_numbers = [203, 204, 205, 208]  # Adjust these numbers based on your requirements

    # Convert the nutrient numbers to a comma-separated string
    nutrients_str = ",".join(map(str, nutrient_numbers))

    # Query API
    try:
        response = requests.get(base_url + f'foods?fdcIds={fdc_ids_str}&api_key={api_key}&nutrients={nutrients_str}')
        data = response.json()

        if data and len(data) > 0:
            # Initialize nutritional_info as a list to store results for multiple foods
            nutritional_info = []

            for food_data in data:
                nutrient_info = {
                    "food_name": food_data.get('description', 'Unknown Food'),
                    "fdc_id": food_data.get('fdcId', 'Unknown ID'),
                    "calories": None,
                    "protein": None,
                    "fat": None,
                    "serving_size": None,
                    "carbs": None
                }

                nutrients = food_data.get('foodNutrients', [])
                for nutrient in nutrients:
                    nutrient_name = nutrient.get('nutrient', {}).get('name')  # Safely access nutrient name
                    if nutrient_name is None:
                        continue

                    nutrient_value = nutrient.get('amount') or nutrient.get('nutrient', {}).get('amount')  # Handle potential nesting
                    unit_name = nutrient.get('nutrient', {}).get('unitName')

                    if nutrient_name == 'Protein' and 203 in nutrient_numbers:
                        nutrient_info["protein"] = f"{nutrient_value} {unit_name}"
                    elif nutrient_name == 'Total lipid (fat)' and 204 in nutrient_numbers:
                        nutrient_info["fat"] = f"{nutrient_value} {unit_name}"
                    elif nutrient_name == 'Carbohydrate, by difference' and 205 in nutrient_numbers:
                        nutrient_info["carbs"] = f"{nutrient_value} {unit_name}"
                    elif nutrient_name == 'Energy' and 208 in nutrient_numbers:
                        nutrient_info["calories"] = f"{nutrient_value} {unit_name}"

                # Append the nutrient_info for this food to the list
                nutritional_info.append(nutrient_info)

            return nutritional_info
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None

def is_float(str):
    try:
        float(str) # converts it to a float data type
        return True
    except ValueError:
        return False

def search_food_branded(q):

    # query the large database for branded
    search_results = db.execute("SELECT * FROM food WHERE description LIKE ?", (q + "%",))
    total_hits = db.execute("SELECT COUNT(*) FROM food WHERE description LIKE ?", (q + "%",))

    return search_results, total_hits

def get_nutritional_info_branded(fdc_ids, page):
    """gets the macros and calories for the individual foods """
    if fdc_ids:
        nutritional_info = []
        # Slice the fdc_ids list to include only the first ten elements
        for i in range(1, page + 1):
            end = i * 10
            initial = (i - 1) * 10
            if end > len(fdc_ids):
                nutritional_info = []
                return nutritional_info
            else:
                fdc_ids = fdc_ids[initial:end]
                for i in fdc_ids:
                    rows = db.execute("SELECT food.description, food_nutrient.nutrient_id, food_nutrient.amount FROM food INNER JOIN food_nutrient ON food.fdc_id = food_nutrient.fdc_id WHERE food.fdc_id = ? AND food_nutrient.nutrient_id IN (1008, 1003, 1004, 1005) ORDER BY nutrient_id DESC", i)
                    if len(rows) == 4:
                        nutrient_info = {
                            "food_name": rows[0]["description"],
                            "calories": rows[0]["amount"],
                            "carbs": rows[1]["amount"],
                            "fat": rows[2]["amount"],
                            "protein": rows[3]["amount"],
                            }
                        nutritional_info.append(nutrient_info)
                    else:
                        for row in rows:
                            nutrient_info = {
                                "food_name": rows[0]["description"],
                                "calories": 0,
                                "carbs": 0,
                                "fat": 0,
                                "protein": 0,
                                }
                            if row["nutrient_id"] == 1008:
                                nutrient_info["calories"] = row["amount"]
                            elif row["nutrient_id"] == 1005:
                                nutrient_info["carbs"] = row["amount"]
                            elif row["nutrient_id"] == 1004:
                                nutrient_info["fat"] = row["amount"]
                            elif row["nutrient_id"] == 1003:
                                nutrient_info["protein"] = row["amount"]

                            nutritional_info.append(nutrient_info)

    return nutritional_info









