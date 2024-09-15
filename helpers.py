import requests
from aiohttp import ClientSession, ClientError
from functools import wraps
from quart import redirect, render_template, url_for, session
from functools import wraps


async def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.
        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return await render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return await f(*args, **kwargs)

    return decorated_function


def is_float(str):
    try:
        float(str)  # converts it to a float data type
        return True
    except ValueError:
        return False


# recommended daily value micro and macro nutrients for adults
daily_values = {
    "Energy": 2000,  # in kcal
    "Total lipid (fat)": 70,  # in g
    "Fatty acids, total saturated": 20,  # in g
    "Fatty acids, total trans": 2,  # in g
    "Cholesterol": 300,  # in mg
    "Sodium, Na": 2300,  # in mg
    "Carbohydrate, by difference": 310,  # in g
    "Fiber, total dietary": 25,  # in g
    "Sugars, total including NLEA": 50,  # in g
    "Protein": 50,  # in g
    "Vitamin A, RAE": 900,  # in µg
    "Vitamin C, total ascorbic acid": 90,  # in mg
    "Vitamin D (D2 + D3)": 20,  # in µg
    "Vitamin E (alpha-tocopherol)": 15,  # in mg
    "Vitamin K (phylloquinone)": 120,  # in µg
    "Thiamin": 1.2,  # in mg
    "Riboflavin": 1.3,  # in mg
    "Niacin": 16,  # in mg
    "Pantothenic acid": 5,  # in mg
    "Vitamin B-6": 1.7,  # in mg
    "Folate, total": 400,  # in µg
    "Vitamin B-12": 2.4,  # in µg
    "Vitamin B-12, added": 2.4,  # in µg
    "Choline, total": 550,  # in mg
    "Vitamin K (Dihydrophylloquinone)": 120,  # in µg
    "Folic acid": 400,  # in µg
    "Folate, food": 400,  # in µg
    "Folate, DFE": 600,  # in µg
    "Betaine": 2000,  # in mg
    "Vitamin E, added": 15,  # in mg
    "Vitamin B-12 (cobalamin)": 2.4,  # in µg
    "Vitamin D": 20,  # in µg
    "Vitamin A": 900,  # in µg
    "Vitamin E": 15,  # in mg
    "Vitamin D2 (ergocalciferol)": 20,  # in µg
    "Vitamin D3 (cholecalciferol)": 20,  # in µg
    "Vitamin A (IU)": 3000,  # in IU
    "Vitamin D (IU)": 800,  # in IU
    "Vitamin E (IU)": 22,  # in IU
    "Vitamin C": 90,  # in mg
    "Biotin": 30,  # in µg
    "Calcium, Ca": 1300,  # in mg
    "Iron, Fe": 18,  # in mg
    "Magnesium, Mg": 420,  # in mg
    "Zinc, Zn": 11,  # in mg
    "Copper, Cu": 0.9,  # in mg
    "Manganese, Mn": 2.3,  # in mg
    "Selenium, Se": 55,  # in µg
    "Chromium, Cr": 35,  # in µg
    "Molybdenum, Mo": 45,  # in µg
    "Chloride, Cl": 2300,  # in mg
    "Potassium, K": 4700,  # in mg
    "Phosphorus, P": 1250,  # in mg
    "Iodine, I": 150,  # in µg
    "Vitamin B-12, added": 2.4,  # in µg
    "Vitamin D (D2 + D3), added": 20,  # in µg
    "Vitamin E (added)": 15,  # in mg
    "Vitamin B-6, added": 1.7,  # in mg
    "Vitamin K (Menaquinone-4)": 120,  # in µg
    "Vitamin K (Menaquinone-7)": 120,  # in µg
    "Vitamin A, added": 900,  # in µg
    "Vitamin C, added": 90,  # in mg
    "Vitamin D2, added": 20,  # in µg
    "Vitamin D3, added": 20,  # in µg
    "Vitamin E, added": 15,  # in mg
    "Vitamin K, added": 120,  # in µg
    "Vitamin B-12 (Cyanocobalamin)": 2.4,  # in µg
}


def validate_registration_form(username, email, password, confirm_pass):
    """Validate the registration form inputs"""
    if not username:
        return "must provide username"
    if not email:
        return "must provide email"
    if not password:
        return "must provide password"
    if not confirm_pass:
        return "must retype password"
    if password != confirm_pass:
        return "Wrong Confirm Password"
    if len(password) < 8 or len(confirm_pass) < 8:
        return "Password must be at least 8 characters"
    return None


async def get_nutritional_info(fdcId, api_key):
    """Look up food's nutrional value."""

    base_url = f"https://api.nal.usda.gov/fdc/v1/food/{fdcId}"
    params = {"api_key": api_key}

    try:
        async with ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                return data

    except (requests.exceptions.RequestException, ValueError, KeyError):
        return None


# deprecated functions
# reason: will now use USDA API to get nutritional info in client side instead of the server side


# async def lookup_nutritional_info(query, api_key):
#     """Look up food's nutrional value."""
#     # USDA FDC API
#     base_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
#     params = {"query": query, "api_key": api_key}
#     # Query API
#     try:
#         async with ClientSession() as session:
#             async with session.get(base_url, params=params) as response:
#                 response.raise_for_status()
#                 data = await response.json()

#                 if "foods" in data and len(data["foods"]) > 0:
#                     food = data["foods"][0]
#                     nutrient_data = food.get("foodNutrients", [])
#                     nutritional_info = {
#                         "name": food.get("description", ""),
#                         "fdc_id": food.get("fdcId", ""),
#                         "serving_size": food.get("servingSize", ""),
#                         "nutrients": [
#                             {
#                                 "name": nutrient["nutrientName"],
#                                 "value": nutrient["value"],
#                                 "unit": nutrient["unitName"],
#                             }
#                             for nutrient in nutrient_data
#                         ],
#                     }
#                     return nutritional_info
#                 else:
#                     return None

#     except (ClientError, ValueError, KeyError):
#         return None


# async def search_food(query, api_key, page, page_size):
#     base_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
#     data_types = ["Survey (FNDDS)", "SR Legacy", "Foundation"]
#     params = {
#         "query": query,
#         "api_key": api_key,
#         "pageNumber": page,
#         "pageSize": page_size,
#         "dataType": data_types,
#         "sortBy": "dataType.keyword",
#     }

#     async with ClientSession() as session:
#         async with session.get(base_url, params=params) as response:
#             response.raise_for_status()  # Raise an exception if there's an HTTP error
#             data = await response.json()
#             total_hits = data.get("totalHits", 0)

#             if "foods" in data:
#                 search_results = [
#                     {
#                         "food_name": food["description"],
#                         "fdc_id": food["fdcId"],
#                     }
#                     for food in data["foods"]
#                 ]

#     return search_results, total_hits


# async def get_nutritional_info(fdc_ids, api_key):
#     base_url = "https://api.nal.usda.gov/fdc/v1/"

#     # Convert the list of fdc_ids to a comma-separated string
#     fdc_ids_str = ",".join(map(str, fdc_ids))

#     # Specify the nutrient numbers you want to retrieve (e.g., 203 for Protein, 204 for Total lipid (fat), etc.)
#     nutrient_numbers = [
#         203,
#         204,
#         205,
#         208,
#     ]  # Adjust these numbers based on your requirements

#     # Convert the nutrient numbers to a comma-separated string
#     nutrients_str = ",".join(map(str, nutrient_numbers))

#     # Query API
#     try:
#         async with ClientSession() as session:
#             async with session.get(
#                 base_url
#                 + f"foods?fdcIds={fdc_ids_str}&api_key={api_key}&nutrients={nutrients_str}"
#             ) as response:
#                 response.raise_for_status()
#                 data = await response.json()

#                 if data and len(data) > 0:
#                     # Initialize nutritional_info as a list to store results for multiple foods
#                     nutritional_info = []

#                     for food_data in data:
#                         nutrient_info = {
#                             "food_name": food_data.get("description", "Unknown Food"),
#                             "fdc_id": food_data.get("fdcId", "Unknown ID"),
#                             "calories": None,
#                             "protein": None,
#                             "fat": None,
#                             "serving_size": None,
#                             "carbs": None,
#                         }

#                         nutrients = food_data.get("foodNutrients", [])
#                         for nutrient in nutrients:
#                             nutrient_name = nutrient.get("nutrient", {}).get("name")
#                             if nutrient_name is None:
#                                 continue

#                             nutrient_value = nutrient.get("amount") or nutrient.get(
#                                 "nutrient", {}
#                             ).get("amount")
#                             unit_name = nutrient.get("nutrient", {}).get("unitName")

#                             if nutrient_name == "Protein" and 203 in nutrient_numbers:
#                                 nutrient_info["protein"] = (
#                                     f"{nutrient_value} {unit_name}"
#                                 )
#                             elif (
#                                 nutrient_name == "Total lipid (fat)"
#                                 and 204 in nutrient_numbers
#                             ):
#                                 nutrient_info["fat"] = f"{nutrient_value} {unit_name}"
#                             elif (
#                                 nutrient_name == "Carbohydrate, by difference"
#                                 and 205 in nutrient_numbers
#                             ):
#                                 nutrient_info["carbs"] = f"{nutrient_value} {unit_name}"
#                             elif nutrient_name == "Energy" and 208 in nutrient_numbers:
#                                 nutrient_info["calories"] = (
#                                     f"{nutrient_value} {unit_name}"
#                                 )

#                         # Append the nutrient_info for this food to the list
#                         nutritional_info.append(nutrient_info)

#                     return nutritional_info
#     except (ClientError, ValueError, KeyError, IndexError):
#         return None

# def search_food_branded(q):

#     # query the large database for branded
#     search_results = db.execute(
#         "SELECT * FROM food WHERE description LIKE ?", (q + "%",)
#     )
#     total_hits = db.execute(
#         "SELECT COUNT(*) FROM food WHERE description LIKE ?", (q + "%",)
#     )

#     return search_results, total_hits


# def get_nutritional_info_branded(fdc_ids, page):
#     """gets the macros and calories for the individual foods"""
#     if fdc_ids:
#         nutritional_info = []
#         # Slice the fdc_ids list to include only the first ten elements
#         for i in range(1, page + 1):
#             end = i * 10
#             initial = (i - 1) * 10
#             if end > len(fdc_ids):
#                 nutritional_info = []
#                 return nutritional_info
#             else:
#                 fdc_ids = fdc_ids[initial:end]
#                 for i in fdc_ids:
#                     rows = db.execute(
#                         "SELECT food.description, food_nutrient.nutrient_id, food_nutrient.amount FROM food INNER JOIN food_nutrient ON food.fdc_id = food_nutrient.fdc_id WHERE food.fdc_id = ? AND food_nutrient.nutrient_id IN (1008, 1003, 1004, 1005) ORDER BY nutrient_id DESC",
#                         i,
#                     )
#                     if len(rows) == 4:
#                         nutrient_info = {
#                             "food_name": rows[0]["description"],
#                             "calories": rows[0]["amount"],
#                             "carbs": rows[1]["amount"],
#                             "fat": rows[2]["amount"],
#                             "protein": rows[3]["amount"],
#                         }
#                         nutritional_info.append(nutrient_info)
#                     else:
#                         for row in rows:
#                             nutrient_info = {
#                                 "food_name": rows[0]["description"],
#                                 "calories": 0,
#                                 "carbs": 0,
#                                 "fat": 0,
#                                 "protein": 0,
#                             }
#                             if row["nutrient_id"] == 1008:
#                                 nutrient_info["calories"] = row["amount"]
#                             elif row["nutrient_id"] == 1005:
#                                 nutrient_info["carbs"] = row["amount"]
#                             elif row["nutrient_id"] == 1004:
#                                 nutrient_info["fat"] = row["amount"]
#                             elif row["nutrient_id"] == 1003:
#                                 nutrient_info["protein"] = row["amount"]

#                             nutritional_info.append(nutrient_info)

#     return nutritional_info
