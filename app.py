import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, url_for, session
from flask_caching import Cache
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from helpers import apology, login_required, lookup_nutritional_info, search_food, get_nutritional_info, is_float, search_food_branded, get_nutritional_info_branded
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO

# Configure application
app = Flask(__name__)
app.debug = True
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure cs50 library to use sqlite database
db = SQL("sqlite:///user.db")

# gets the current date/time
current_date = datetime.now()
year = current_date.year
month = current_date.month
day = current_date.day
hour = current_date.hour
minute = current_date.minute

# API KEY for USDA food database
api_key = "wz0xIrmQfTqOYmpoeJlHB7UCNyLR3VyqoqUT30Bp"

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """ displays search form"""
    if request.method == "POST":
        query = request.form.get("q")

        # long string or words not accepted
        if len(query) > 30:
            return apology("String length Error", 404)
        # Redirect to the results page with the search query
        return redirect(url_for("results", q=query))
    else:
        return render_template("index.html")

@app.route("/results", methods=["GET"])
@login_required
def results():
    """ returns lists of food for matched query"""
    query = request.args.get("q")
    page = request.args.get('page', 1, type=int)
    page_size = 6  # Define your desired page size here
    fdc_ids = [] # list to store our fdc id

    if not query:
        return apology("Query parameter missing", 400)

    # searches food with pagination
    results, total_hits = search_food(query, api_key, page=page, page_size=page_size)
    total_pages = -(-total_hits // page_size)  # Calculate total pages, use double negative for ceiling division

    # check if user has typed something
    if results and query:
        nutritional_info = []
        for result in results:
            fdc_ids.append(result["fdc_id"]) # append just the fdc id to our list

        # send the request to USDA API using this function
        foods = get_nutritional_info(fdc_ids, api_key)

        if foods:
            for food in foods:
                nutritional_info.append({
                    "food_name": food["food_name"],
                    "fdc_id": food["fdc_id"],
                    "calories": food["calories"],
                    "protein": food["protein"],
                    "fat": food["fat"],
                    "carbs": food["carbs"]
                })

            return render_template("results.html", results=nutritional_info, query=query, page=page, page_size=page_size, total_pages=total_pages)
        else:
            return apology("Sorry, something went wrong", 400)
    else:
        return render_template("results.html",query=query)

@cache.cached(timeout=600, key_prefix=lambda: request.args.get("q"))

@app.route("/results_branded", methods=["GET"])
@login_required
def results_branded():
    """ returns list of food for matched query but BRANDED data type """
    page = request.args.get('page', 1, type=int)
    query = request.args.get("q")
    page_size = 6
    fdc_ids = []


    if not query:
        return apology("Query parameter missing", 400)

    results, total_hits = search_food_branded(query)
    total_pages = -(-len(total_hits) // page_size)  # Calculate total pages, use double negative for ceiling division


    if results:
        nutritional_info = []
        for result in results:
            fdc_ids.append(result["fdc_id"])

        foods = get_nutritional_info_branded(fdc_ids, page)

        if foods:
            for food in foods:
                nutritional_info.append({
                    "food_name": food["food_name"],
                    "calories": food["calories"],
                    "protein": food["protein"],
                    "fat": food["fat"],
                    "carbs": food["carbs"]
                })

            return render_template("results-branded.html", results=nutritional_info, query=query, page=page, page_size=15, total_pages=total_pages)

        else:
            return apology("Sorry, there is no more data to show.", 404)

    else:
        return apology("No match found", 404)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """register user"""

    # user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_pass = request.form.get("confirm_password")

        # if username has no input return an apology
        if not username:
            return apology("must provide username", 400)

        # if password has no input return an apology
        elif not password:
            return apology("must provide password", 400)

        elif not confirm_pass:
            return apology("must retype password", 400)

        elif password != confirm_pass:
            return apology("Wrong Confirm Password", 400)

        elif len(password) < 8 or len(confirm_pass) < 8:
            return apology("Password must be at least 8 characters")

        # execute a sql line to load user's username
        user_check = db.execute(
            "SELECT username FROM users WHERE username = ?", username
        )

        # check if the username is taken using user_check
        if user_check:
            return apology("Username already taken", 400)

        # hashes the plain-text password
        hashed_password = generate_password_hash(password)

        # add the newly registered user into our database
        db.execute(
            "INSERT INTO users (username, hash) VALUES(?, ?)", username, hashed_password
        )

        # log in our newly registered user into the website
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if rows:
            session["user_id"] = rows[0]["id"]

        flash("Registered!", "success")
        return redirect("/")

    # User reached route via GET (as by clicking register or via redirect)
    else:
        return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/details", methods=["GET", "POST"])
@login_required
def result():
    """ display's the selected food's nutrition facts """
    food = request.form.get("food_name")
    result=lookup_nutritional_info(food, api_key)

    nutrients = {}
    if result is not None:
        for nutrient in result.get("nutrients", []):
            nutrients[nutrient["name"]] = {
                "value": nutrient["value"],
                "unit": nutrient["unit"]
            }

    # recommended daily value micro and macro nutrients for adults
    daily_values = {
        'Energy': 2000,  # in kcal
        'Total lipid (fat)': 70,  # in g
        'Fatty acids, total saturated': 20,  # in g
        'Fatty acids, total trans': 2,  # in g
        'Cholesterol': 300,  # in mg
        'Sodium, Na': 2300,  # in mg
        'Carbohydrate, by difference': 310,  # in g
        'Fiber, total dietary': 25,  # in g
        'Sugars, total including NLEA': 50,  # in g
        'Protein': 50,  # in g
        'Vitamin A, RAE': 900,  # in µg
        'Vitamin C, total ascorbic acid': 90,  # in mg
        'Vitamin D (D2 + D3)': 20,  # in µg
        'Vitamin E (alpha-tocopherol)': 15,  # in mg
        'Vitamin K (phylloquinone)': 120,  # in µg
        'Thiamin': 1.2,  # in mg
        'Riboflavin': 1.3,  # in mg
        'Niacin': 16,  # in mg
        'Pantothenic acid': 5,  # in mg
        'Vitamin B-6': 1.7,  # in mg
        'Folate, total': 400,  # in µg
        'Vitamin B-12': 2.4,  # in µg
        'Vitamin B-12, added': 2.4,  # in µg
        'Choline, total': 550,  # in mg
        'Vitamin K (Dihydrophylloquinone)': 120,  # in µg
        'Folic acid': 400,  # in µg
        'Folate, food': 400,  # in µg
        'Folate, DFE': 600,  # in µg
        'Betaine': 2000,  # in mg
        'Vitamin E, added': 15,  # in mg
        'Vitamin B-12 (cobalamin)': 2.4,  # in µg
        'Vitamin D': 20,  # in µg
        'Vitamin A': 900,  # in µg
        'Vitamin E': 15,  # in mg
        'Vitamin D2 (ergocalciferol)': 20,  # in µg
        'Vitamin D3 (cholecalciferol)': 20,  # in µg
        'Vitamin A (IU)': 3000,  # in IU
        'Vitamin D (IU)': 800,  # in IU
        'Vitamin E (IU)': 22,  # in IU
        'Vitamin C': 90,  # in mg
        'Biotin': 30,  # in µg
        'Calcium, Ca': 1300,  # in mg
        'Iron, Fe': 18,  # in mg
        'Magnesium, Mg': 420,  # in mg
        'Zinc, Zn': 11,  # in mg
        'Copper, Cu': 0.9,  # in mg
        'Manganese, Mn': 2.3,  # in mg
        'Selenium, Se': 55,  # in µg
        'Chromium, Cr': 35,  # in µg
        'Molybdenum, Mo': 45,  # in µg
        'Chloride, Cl': 2300,  # in mg
        'Potassium, K': 4700,  # in mg
        'Phosphorus, P': 1250,  # in mg
        'Iodine, I': 150,  # in µg
        'Vitamin B-12, added': 2.4,  # in µg
        'Vitamin D (D2 + D3), added': 20,  # in µg
        'Vitamin E (added)': 15,  # in mg
        'Vitamin B-6, added': 1.7,  # in mg
        'Vitamin K (Menaquinone-4)': 120,  # in µg
        'Vitamin K (Menaquinone-7)': 120,  # in µg
        'Vitamin A, added': 900,  # in µg
        'Vitamin C, added': 90,  # in mg
        'Vitamin D2, added': 20,  # in µg
        'Vitamin D3, added': 20,  # in µg
        'Vitamin E, added': 15,  # in mg
        'Vitamin K, added': 120,  # in µg
        'Vitamin B-12 (Cyanocobalamin)': 2.4,  # in µg
        }

    
    return render_template("result.html", result=result, nutrient=nutrients, daily_values=daily_values)


@app.route("/food-log", methods=["GET", "POST"])
@login_required
def food_log():
    """ User's food log or diet history """
    food = request.form.get("food")
    calorie = request.form.get("Energy")
    protein = request.form.get("Protein")
    carbs = request.form.get("Carbohydrate, by difference")
    fat = request.form.get("Total lipid (fat)")


    if calorie is not None and protein is not None and carbs is not None and fat is not None:
        try:
            calorie = float(calorie)
            protein = float(protein)
            carbs = float(carbs)
            fat = float(fat)
        except ValueError:
            return apology("Error invalid values!", 400)
        
        if not is_float(calorie) or not is_float(protein) or not is_float(carbs) or not is_float(fat):
            return apology("Error invalid values!", 400)

        if int(calorie) < 0 or float(protein) < 0 or float(carbs) < 0 or float(fat) < 0:
            return apology("Error Negative value detected!", 400)




    # Calcuate the date for last sunday (start of the week)
    prev_sunday = current_date - timedelta(days=current_date.weekday() + 1)

    # Initialize a list to store the dates for the entire week
    week_dates = []

    for i in range(7):
        day_date = prev_sunday + timedelta(days=i)
        week_dates.append({
            "month": day_date.month,
            "day": day_date.day,
            "year": day_date.year
        })

    # if user reached POST (as by submitting a form via POST)
    if request.method == "POST":

        # if the user has submitted with values for these nutrients.
        if food:

            # insert these values into our database
            db.execute("INSERT INTO food_count(user_id, food_name, calories, protein, carbs, fat, month, day, year, hour, minute) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", session["user_id"], food, calorie, protein, carbs, fat, month, day, year, hour, minute)

            return redirect("/")

        else:
            return apology("Error", 400)

    # if the user reached GET (as by clicking food_log)
    else:
        # store our queries in a list

        food_log_query = []
        # get the user's food intake for the last 7 days
        for i in range(7):
            food_log_query.append(db.execute("SELECT SUM(COALESCE(calories, 0)) AS total_calories, SUM(COALESCE(protein, 0)) AS total_protein, SUM(COALESCE(carbs, 0)) AS total_carbs, SUM(COALESCE(fat, 0)) AS total_fat FROM food_count WHERE user_id = ? AND month = ? AND day = ? AND year = ?", session["user_id"], week_dates[i]["month"], week_dates[i]["day"], week_dates[i]["year"]))

        # Initialize variables to handle no data case
        food_log = None
        graph_url = None

        # checks if the query has some content.
        if food_log_query:
            # bar graph implementation
            # our x coordinate
            week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

            # per day retrieve the total calories and macros
            # Initialize lists to store the totals for each day
            total_calories = []
            total_protein = []
            total_carbs = []
            total_fat = []

            # Loop through the queries (one query for each day)
            for query_result in food_log_query:
                # Initialize daily totals for this query result
                daily_total_calories = 0
                daily_total_protein = 0
                daily_total_carbs = 0
                daily_total_fat = 0

                # Loop through the dictionaries in the query result
                for result in query_result:
                    # Add values from this dictionary to the daily totals, but check for None values first
                    daily_total_calories += result["total_calories"] if result["total_calories"] is not None else 0
                    daily_total_protein += result["total_protein"] if result["total_protein"] is not None else 0
                    daily_total_carbs += result["total_carbs"] if result["total_carbs"] is not None else 0
                    daily_total_fat += result["total_fat"] if result["total_fat"] is not None else 0

                # Append the daily totals to the respective lists
                total_calories.append(daily_total_calories)
                total_protein.append(daily_total_protein)
                total_carbs.append(daily_total_carbs)
                total_fat.append(daily_total_fat)

            # calculates the max data
            max_value = max(total_calories)
            y_max = max_value + 50

            # Increase the figure width here
            plt.figure(figsize=(10, 6))  # Adjusts the width and height

            # set the y-axis label limit
            plt.ylim(0, y_max)

            # array([0, 1, 2, 3, 4])
            xpos = np.arange(len(week))
            plt.xticks(xpos, week)
            plt.ylabel("Gram weight or KCAL")
            plt.title("Calories and macros throughout the week")
            plt.bar(xpos-0.1, total_calories, width=0.4, label="Calories")
            plt.bar(xpos-0.1, total_protein, width=0.4, label="protein")
            plt.bar(xpos+0.2, total_carbs, width=0.2, label="Carbs")
            plt.bar(xpos+0.4, total_fat, width=0.2, label="Fat")
            plt.legend()

            # Save the plot as a PNG image
            buffer = BytesIO()
            plt.savefig(buffer, format="png")
            buffer.seek(0)
            graph_url = base64.b64encode(buffer.getvalue()).decode()


        return render_template("food-log.html", food_log=food_log, graph_url=graph_url)

if __name__ == "__main__":
    app.run()