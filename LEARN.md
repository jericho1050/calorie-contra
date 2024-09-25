# Calorie Contra

## Demo

[![Calorie Contra](https://imgur.com/Eroy6fD.jpg)](https://www.youtube.com/watch?v=YbvBbK3sb_M)

## Description

This calorie counter and food search web app is for individuals who want to track their calories and macros throughout the day and week. For searching data, it uses a REST API from the USDA [FDC API](https://fdc.nal.usda.gov/api-spec/fdc_api.html). It is also embedded with a chatbot that helps you achieve your goals.

## Testimony

It all started as a final project for CS50X and as a first web app project, but then looking back at how it was terribly implemented, I decided to revisit this project and redesgin and refactor the codes and functionality. The project isn't that crazy good, but I'm kind of proud of what I did here, and there's still more room for improvements and more features to implement. Hopefully someday the web app will be useful and be monetized.

## Usage

1. **Clone this repository**

    ```sh
    git clone https://github.com/jericho1050/calorie-contra.git
    ```

2. **Create a virtual environment**

    ```sh
    virtualenv env
    ```

    or

    ```sh
    python -m venv env
    ```

    then activate it

    ```sh
    # MacOS
    source env/bin/activate
    ```

    ```sh
    # Windows
    .\env\Scripts\activate
    ```

3. **Install the dependencies**

    ```sh
    pip install -r requirements.txt
    ```

4. **Create a [`.env`](command:_github.copilot.openRelativePath?%5B%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2FUsers%2Fjerichowenzel%2FDownloads%2Fcalorie_contra%2F.env%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22f9f02ad9-8067-44a1-a645-88b840a6cfe0%22%5D "/Users/jerichowenzel/Downloads/calorie_contra/.env") file for API keys and secret variables**

    ```sh
    # .env
    api_key = "your_api_key_here" # https://fdc.nal.usda.gov/api-key-signup.html
    SECRET_KEY = "your_secret_key_here" 
    gemini_api_key = "your_api_key_here" # https://ai.google.dev
    ```

5. **Run the server**

    ```sh
    python app.py
    ```

## Walkthrough

### `app.py` Routes

#### `/home` (GET, POST)

- **Purpose**: Displays the search form and handles search queries.
- **Methods**:
  - `GET`: Renders the home page.
  - `POST`: Processes the search query and redirects to the search results.

#### `/search` (GET)

- **Purpose**: Returns a list of foods matching the search query.
- **Methods**:
  - `GET`: Renders the search results page.

#### `/api/search_foods` (GET)

- **Purpose**: API endpoint to search for foods using the USDA FoodData Central API.
- **Methods**:
  - `GET`: Returns JSON data of the search results.

#### `/login` (GET, POST)

- **Purpose**: Logs the user in.
- **Methods**:
  - `GET`: Renders the login page.
  - `POST`: Authenticates the user and starts a session.

#### `/register` (GET, POST)

- **Purpose**: Registers a new user.
- **Methods**:
  - `GET`: Renders the registration page.
  - `POST`: Processes the registration form and creates a new user.

#### `/logout` (GET)

- **Purpose**: Logs the user out.
- **Methods**:
  - `GET`: Clears the session and redirects to the home page.

#### `/food/<int:id>` (GET)

- **Purpose**: Displays the selected food's nutrition facts.
- **Methods**:
  - `GET`: Renders the food details page.

#### `/food-log` (GET, POST)

- **Purpose**: Displays and updates the user's food log.
- **Methods**:
  - `GET`: Renders the food log page.
  - `POST`: Adds a new food entry to the user's log.

#### `/generate` (POST)

- **Purpose**: Generates a response using the generative AI model.
- **Methods**:
  - `POST`: Processes the user's input and returns the AI-generated response.

## Test

TODO

## Contribution Guideline

TODO
