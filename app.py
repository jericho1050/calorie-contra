import os, quart_flask_patch
from quart import Quart, flash, redirect, render_template, request, url_for, session

# from flask_caching import Cache
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from helpers import (
    apology,
    login_required,  # Ensure this is the updated decorator
    is_float,
    daily_values,
    validate_registration_form,
    get_nutritional_info,
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
app = Quart(__name__)
app.debug = True


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db_session = scoped_session(SessionLocal)

api_key = os.getenv("api_key")


@app.before_serving
async def startup():
    await setup_database()


@app.after_request
async def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/home", methods=["GET", "POST"])
async def index():
    """displays search form"""
    if request.method == "POST":
        query = (await request.form).get("q")

        # long string or words not accepted
        if len(query) > 30:
            return await apology("String length Error", 404)
        # Redirect to the results page with the search query
        return redirect(url_for("search"))
    else:
        return await render_template("home.html")


@app.route("/search", methods=["GET"])
@login_required
async def search():
    """returns lists of food for matched query"""
    query = request.args.get("q")

    return await render_template("search_foods.html", query=query, api_key=api_key)


@app.route("/login", methods=["GET", "POST"])
async def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        form = await request.form
        # Ensure username was submitted
        if not form.get("username"):
            return await apology("must provide username", 403)

        # Ensure password was submitted
        elif not form.get("password"):
            return await apology("must provide password", 403)

        # Query database for username
        username = form.get("username")
        password = form.get("password")

        try:
            stmt = select(User).where(User.username == username)
            result = await db_session.execute(stmt)
            user = result.scalar_one()

            # Ensure username exists and password is correct
            if not check_password_hash(user.hash, password):
                return await apology("invalid username and/or password", 403)

            # Remember which user has logged in
            session["user_id"] = user.id

            # Redirect user to home page
            return redirect("/home")

        except NoResultFound:
            return await apology("invalid username and/or password", 403)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return await render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
async def register():
    """register user"""

    # user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        form = await request.form
        username = form.get("username")
        email = form.get("email")
        password = form.get("password")
        confirm_pass = form.get("confirm_password")

        error_message = validate_registration_form(
            username, email, password, confirm_pass
        )
        if error_message:
            apology(error_message, 400)

        try:
            stmt = select(User).where(User.username == username)
            result = await db_session.execute(stmt)
            user_check = result.scalar_one_or_none()

            # check if the username is taken using user_check
            if user_check:
                return await apology("Username already taken", 400)

            # hashes the plain-text password
            hashed_password = generate_password_hash(password)

            # Add the newly registered user to the database
            new_user = User(username=username, email=email, hash=hashed_password)
            db_session.add(new_user)
            await db_session.commit()

            # log in our newly registered user into the website
            session["user_id"] = new_user.id

            await flash("Registered!", "success")
            return redirect("/home")

        except IntegrityError:
            await db_session.rollback()
            return await apology("Username already taken", 400)

    # User reached route via GET (as by clicking register or via redirect)
    else:
        return await render_template("register.html")


@app.route("/logout")
async def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/home")


@app.route("/food/<int:id>", methods=["GET"])
@login_required
async def food(id):
    """display's the selected food's nutrition facts"""

    food = await get_nutritional_info(id, api_key)

    return await render_template("food.html", food=food)


@app.route("/food-log", methods=["GET", "POST"])
@login_required
async def food_log():
    """User's food log or diet history"""
    form = await request.form
    food = form.get("food")
    calorie = form.get("Energy")
    protein = form.get("Protein")
    carbs = form.get("Carbohydrate, by difference")
    fat = form.get("Total lipid (fat)")

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
            return await apology("Error invalid values!", 400)

        if (
            not is_float(calorie)
            or not is_float(protein)
            or not is_float(carbs)
            or not is_float(fat)
        ):
            return await apology("Error invalid values!", 400)

        if int(calorie) < 0 or float(protein) < 0 or float(carbs) < 0 or float(fat) < 0:
            return await apology("Error Negative value detected!", 400)

    # Calculate the date for last Sunday (start of the week)
    current_date = datetime.now()
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
            await db_session.execute(stmt)
            await db_session.commit()

            return redirect("/")

        else:
            return await apology("Error", 400)

    # if the user reached GET (as by clicking food_log)
    else:
        # store our queries in a list
        food_log_query = []
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
            result = await db_session.execute(stmt)
            food_log_query.append(result.fetchone())

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
            for result in food_log_query:
                # Append the daily totals to the respective lists
                total_calories.append(result.total_calories or 0)
                total_protein.append(result.total_protein or 0)
                total_carbs.append(result.total_carbs or 0)
                total_fat.append(result.total_fat or 0)

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

        return await render_template(
            "food-log.html", food_log=food_log, graph_url=graph_url
        )


if __name__ == "__main__":
    app.run(debug=True)
