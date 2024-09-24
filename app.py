import os
import json
import quart_flask_patch
from quart import (
    Quart,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    session,
    jsonify,
)
import requests

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
from matplotlib.animation import FuncAnimation
import numpy as np
import base64
from io import BytesIO
from dotenv import load_dotenv
import google.generativeai as genai
from sqlalchemy.orm import scoped_session
from sqlalchemy import select, insert, func
from sqlalchemy.exc import NoResultFound, IntegrityError
from database import setup_database, SessionLocal, User, FoodCount


load_dotenv()  # load the environment variables
genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)  # configure the API key for generative AI
model = genai.GenerativeModel(
    "gemini-1.5-flash",
    system_instruction="You are a knowledgeable nutritionist specializing in health, fitness, nutrition, and diet. You assist users in tracking calories and macronutrients, using data from various sources, including the USDA FoodData Central (FDC) API, to provide accurate food information. Help users search for foods, log their intake, adjust serving sizes, and offer tailored advice for dietary goals such as weight loss, muscle gain, or maintenance. Your response must be short and concise, and your tone must be motivating. Limit all responses to topics related to health, fitness, nutrition, or diet. If a question is not related to health, fitness, nutrition, or diet, please respond with 'I'm sorry, I can only provide information on health, fitness, nutrition, or diet.'",
)


# Configure application
app = Quart(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db_session = scoped_session(SessionLocal)

api_key = os.getenv("API_KEY")


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


@app.route("/api/search_foods", methods=["GET"])
async def search_foods():
    query = request.args.get("query")
    page = request.args.get("page", 1)
    data_type = request.args.get("dataType", "")

    if not query:
        return {"error": "Query parameter is required"}

    try:
        base_url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={api_key}&query={query}"
        page_param = f"&pageNumber={page}"
        data_type_param = f"&dataType={data_type}" if data_type else ""
        url = f"{base_url}{data_type_param}{page_param}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return jsonify(data)
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


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

    # Calculate the date for last Sunday (start of the week)
    current_date = datetime.now()

    # if user reached POST (as by submitting a form via POST)
    if request.method == "POST":
        data = await request.get_json()
        food = data.get("food")
        calorie = data.get("calories")
        protein = data.get("protein")
        carbs = data.get("carbs")
        fat = data.get("fat")

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

            if (
                int(calorie) < 0
                or float(protein) < 0
                or float(carbs) < 0
                or float(fat) < 0
            ):
                return await apology("Error Negative value detected!", 400)

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

            return {"message": "success"}

        else:
            return await apology("Error", 400)

    # if the user reached GET (as by clicking food_log)
    else:
        # Get the selected date from the form or use the current date as default
        selected_date_str = request.args.get("selected_date")
        if selected_date_str:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d")
        else:
            selected_date = datetime.now()

        prev_sunday = selected_date - timedelta(days=selected_date.weekday() + 1)
        week_dates = []
        # Initialize a list to store the dates for the entire week
        for i in range(7):
            day_date = prev_sunday + timedelta(days=i)
            week_dates.append(
                {"month": day_date.month, "day": day_date.day, "year": day_date.year}
            )

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
        graph_html = None

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
            # Generate date labels
            date_labels = []

            # Loop through the queries (one query for each day)
            for i, result in enumerate(food_log_query):
                # Append the daily totals to the respective lists
                total_calories.append(result.total_calories or 0)
                total_protein.append(result.total_protein or 0)
                total_carbs.append(result.total_carbs or 0)
                total_fat.append(result.total_fat or 0)

                # Generate the date label for the current day
                date = prev_sunday + timedelta(days=i)
                date_label = f"{week[i]}\n{date.strftime('%m-%d-%y')}"
                date_labels.append(date_label)

            # calculates the max data
            max_value = max(total_calories)
            y_max = max_value + 50

            # Increase the figure width here
            fig, ax = (
                plt.figure(figsize=(10, 6)),
                plt.gca(),
            )  # Adjusts the width and height

            # set the y-axis label limit
            ax.set_ylim(0, y_max)

            # array([0, 1, 2, 3, 4])
            xpos = np.arange(len(week))
            bars_calories = ax.bar(
                xpos - 0.1, total_calories, width=0.4, label="Calories"
            )
            bars_protein = ax.bar(xpos - 0.1, total_protein, width=0.4, label="protein")
            bars_carbs = ax.bar(xpos + 0.2, total_carbs, width=0.2, label="Carbs")
            bars_fat = ax.bar(xpos + 0.4, total_fat, width=0.2, label="Fat")
            ax.set_xticks(xpos)
            ax.set_xticklabels(date_labels)
            ax.set_ylabel("Gram weight or KCAL")
            ax.set_title("Calories and macros throughout the week")
            ax.legend()

            # Add text annotations for each bar
            def add_annotations(bars, values):
                for bar, value in zip(bars, values):
                    if value > 0:  # Only annotate if the value is greater than 0
                        height = bar.get_height()
                        ax.text(
                            bar.get_x() + bar.get_width() / 2,
                            height,
                            f"{value:.0f}",
                            ha="center",
                            va="bottom",
                        )

            add_annotations(bars_calories, total_calories)
            add_annotations(bars_protein, total_protein)
            add_annotations(bars_carbs, total_carbs)
            add_annotations(bars_fat, total_fat)

            # Animation function
            def animate(i):
                for bar, height in zip(bars_calories, total_calories):
                    bar.set_height(height * i / 100)
                for bar, height in zip(bars_protein, total_protein):
                    bar.set_height(height * i / 100)
                for bar, height in zip(bars_carbs, total_carbs):
                    bar.set_height(height * i / 100)
                for bar, height in zip(bars_fat, total_fat):
                    bar.set_height(height * i / 100)

            # Create animation
            anim = FuncAnimation(fig, animate, frames=100, interval=20, repeat=False)

            # Generate HTML representation of the animation
            graph_html = anim.to_jshtml(fps=30, embed_frames=True)

        return await render_template(
            "food-log.html",
            food_log=food_log,
            graph_html=graph_html,
            selected_date=selected_date_str,
        )


@app.route("/generate", methods=["POST"])
async def generate():
    """Generate a text using the generative AI model"""
    data = await request.get_json()
    if data is None or "prompt" not in data:
        return jsonify({"error": "Invalid input"}), 400

    prompt = data["prompt"]

    # Initialize chat history if not present
    if "chat_history" not in session:
        session["chat_history"] = [
            {"role": "user", "parts": "Hello"},
            {
                "role": "model",
                "parts": "Great to meet you. What would you like to know?",
            },
        ]

    # Add the user's message to the chat history
    session["chat_history"].append({"role": "user", "parts": prompt})

    # Start a chat with the current history
    chat = model.start_chat(history=session["chat_history"])

    # Generate a response
    response = await chat.send_message_async(prompt)

    # Add the model's response to the chat history
    session["chat_history"].append({"role": "model", "parts": response.text})

    return jsonify({"text": response.text})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port)