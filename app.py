import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, url_for, session
from flask_caching import Cache
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from helpers import (
    apology,
    login_required,
    lookup_nutritional_info,
    search_food,
    get_nutritional_info,
    is_float,
    search_food_branded,
    get_nutritional_info_branded,
    daily_values,
)
import matplotlib

matplotlib.use("agg")
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO
from dotenv import load_dotenv
from sqlalchemy.orm import scoped_session
from sqlalchemy import select, insert, func
from sqlalchemy.exc import NoResultFound, IntegrityError
from database import setup_database, SessionLocal, User, FoodCount

load_dotenv()

# Configure application
app = Flask(__name__)
app.debug = True
cache = Cache(app, config={"CACHE_TYPE": "simple"})

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up the database
setup_database()

# Create a scoped session for database operations
db_session = scoped_session(SessionLocal)

# gets the current date/time
current_date = datetime.now()
year = current_date.year
month = current_date.month
day = current_date.day
hour = current_date.hour
minute = current_date.minute

# API KEY for USDA food dataset
api_key = os.getenv("api_key")


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
    """displays search form"""
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
    """returns lists of food for matched query"""
    query = request.args.get("q")
    page = request.args.get("page", 1, type=int)
    page_size = 6  # Define your desired page size here
    fdc_ids = []  # list to store our fdc id

    if not query:
        return apology("Query parameter missing", 400)

    # searches food with pagination
    results, total_hits = search_food(query, api_key, page=page, page_size=page_size)
    total_pages = -(
        -total_hits // page_size
    )  # Calculate total pages, use double negative for ceiling division

    # check if user has typed something
    if results and query:
        nutritional_info = []
        for result in results:
            fdc_ids.append(result["fdc_id"])  # append just the fdc id to our list

        # send the request to USDA API using this function
        foods = get_nutritional_info(fdc_ids, api_key)

        if foods:
            for food in foods:
                nutritional_info.append(
                    {
                        "food_name": food["food_name"],
                        "fdc_id": food["fdc_id"],
                        "calories": food["calories"],
                        "protein": food["protein"],
                        "fat": food["fat"],
                        "carbs": food["carbs"],
                    }
                )

            return render_template(
                "results.html",
                results=nutritional_info,
                query=query,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )
        else:
            return apology("Sorry, something went wrong", 400)
    else:
        return render_template("results.html", query=query)


@cache.cached(timeout=600, key_prefix=lambda: request.args.get("q"))
@app.route("/results_branded", methods=["GET"])
@login_required
def results_branded():
    """returns list of food for matched query but BRANDED data type"""
    page = request.args.get("page", 1, type=int)
    query = request.args.get("q")
    page_size = 6
    fdc_ids = []

    if not query:
        return apology("Query parameter missing", 400)

    results, total_hits = search_food_branded(query)
    total_pages = -(
        -len(total_hits) // page_size
    )  # Calculate total pages, use double negative for ceiling division

    if results:
        nutritional_info = []
        for result in results:
            fdc_ids.append(result["fdc_id"])

        foods = get_nutritional_info_branded(fdc_ids, page)

        if foods:
            for food in foods:
                nutritional_info.append(
                    {
                        "food_name": food["food_name"],
                        "calories": food["calories"],
                        "protein": food["protein"],
                        "fat": food["fat"],
                        "carbs": food["carbs"],
                    }
                )

            return render_template(
                "results-branded.html",
                results=nutritional_info,
                query=query,
                page=page,
                page_size=15,
                total_pages=total_pages,
            )

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
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            stmt = select(User).where(User.username == username)
            user = db_session.execute(stmt).scalar_one()

            # Ensure username exists and password is correct
            if not check_password_hash(user.hashed_password, password):
                return apology("invalid username and/or password", 403)

            # Remember which user has logged in
            session["user_id"] = user.id

            # Redirect user to home page
            return redirect("/")

        except NoResultFound:
            return apology("invalid username and/or password", 403)

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

        try:
            stmt = select(User).where(User.username == username)
            user_check = db_session.execute(stmt).scalar_one()

            # check if the username is taken using user_check
            if user_check:
                return apology("Username already taken", 400)

            # hashes the plain-text password
            hashed_password = generate_password_hash(password)

            # Add the newly registered user to the database
            new_user = User(username=username, hashed_password=hashed_password)
            db_session.add(new_user)
            db_session.commit()

            # log in our newly registered user into the website
            session["user_id"] = new_user.id

            flash("Registered!", "success")
            return redirect("/")

        except IntegrityError:
            db_session.rollback()
            return apology("Username already taken", 400)

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
    """display's the selected food's nutrition facts"""
    food = request.form.get("food_name")
    result = lookup_nutritional_info(food, api_key)

    nutrients = {}
    if result is not None:
        for nutrient in result.get("nutrients", []):
            nutrients[nutrient["name"]] = {
                "value": nutrient["value"],
                "unit": nutrient["unit"],
            }
    return render_template(
        "result.html", result=result, nutrient=nutrients, daily_values=daily_values
    )


@app.route("/food-log", methods=["GET", "POST"])
@login_required
def food_log():
    """User's food log or diet history"""
    food = request.form.get("food")
    calorie = request.form.get("Energy")
    protein = request.form.get("Protein")
    carbs = request.form.get("Carbohydrate, by difference")
    fat = request.form.get("Total lipid (fat)")

    if (
        calorie is not None
        and protein is not None
        and carbs is not None
        and fat is not None
    ):
        try:
            calorie = float(calorie)
            protein = float(protein)
            carbs = float(carbs)
            fat = float(fat)
        except ValueError:
            return apology("Error invalid values!", 400)

        if (
            not is_float(calorie)
            or not is_float(protein)
            or not is_float(carbs)
            or not is_float(fat)
        ):
            return apology("Error invalid values!", 400)

        if int(calorie) < 0 or float(protein) < 0 or float(carbs) < 0 or float(fat) < 0:
            return apology("Error Negative value detected!", 400)

    # Calcuate the date for last sunday (start of the week)
    prev_sunday = current_date - timedelta(days=current_date.weekday() + 1)

    week_dates = []
    # Initialize a list to store the dates for the entire week
    for i in range(7):
        day_date = prev_sunday + timedelta(days=i)
        week_dates.append(
            {"month": day_date.month, "day": day_date.day, "year": day_date.year}
        )

    # if user reached POST (as by submitting a form via POST)
    if request.method == "POST":

        # if the user has submitted with values for these nutrients.
        if food:
            # insert these values into our database
            stmt = insert(FoodCount).values(
                user_id=session["user_id"],
                food_name=food,
                calories=calorie,
                protein=protein,
                carbs=carbs,
                fat=fat,
                month=current_date.month,
                day=current_date.day,
                year=current_date.year,
                hour=current_date.hour,
                minute=current_date.minute,
            )
            db_session.execute(stmt)
            db_session.commit()

            return redirect("/")

        else:
            return apology("Error", 400)

    # if the user reached GET (as by clicking food_log)
    else:
        # store our queries in a list

        food_log_query = []
        # get the user's food intake for the last 7 days
        # get the user's food intake for the last 7 days
        for date in week_dates:
            stmt = select(
                func.sum(FoodCount.calories).label("total_calories"),
                func.sum(FoodCount.protein).label("total_protein"),
                func.sum(FoodCount.carbs).label("total_carbs"),
                func.sum(FoodCount.fat).label("total_fat"),
            ).where(
                FoodCount.user_id == session["user_id"],
                FoodCount.month == date["month"],
                FoodCount.day == date["day"],
                FoodCount.year == date["year"],
            )
        # Initialize variables to handle no data case
        food_log = None
        graph_url = None

        # checks if the query has some content.
        if food_log_query:
            # bar graph implementation
            # our x coordinate
            week = [
                "Sunday",
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
            ]

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
                    daily_total_calories += (
                        result["total_calories"]
                        if result["total_calories"] is not None
                        else 0
                    )
                    daily_total_protein += (
                        result["total_protein"]
                        if result["total_protein"] is not None
                        else 0
                    )
                    daily_total_carbs += (
                        result["total_carbs"]
                        if result["total_carbs"] is not None
                        else 0
                    )
                    daily_total_fat += (
                        result["total_fat"] if result["total_fat"] is not None else 0
                    )

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
            plt.bar(xpos - 0.1, total_calories, width=0.4, label="Calories")
            plt.bar(xpos - 0.1, total_protein, width=0.4, label="protein")
            plt.bar(xpos + 0.2, total_carbs, width=0.2, label="Carbs")
            plt.bar(xpos + 0.4, total_fat, width=0.2, label="Fat")
            plt.legend()

            # Save the plot as a PNG image
            buffer = BytesIO()
            plt.savefig(buffer, format="png")
            buffer.seek(0)
            graph_url = base64.b64encode(buffer.getvalue()).decode()

        return render_template("food-log.html", food_log=food_log, graph_url=graph_url)


if __name__ == "__main__":
    app.run()
