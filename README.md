# Calorie Contra

## Video Demo: [link](https://www.youtube.com/watch?v%253DrTQ18UzFF-8)

### Description:This calorie counter and food search web apphas a login/register feature for individuals who want to track their calories and macros throughout the day and week. For searching data, I used a REST API from the USDA FDC [FDC API](https://fdc.nal.usda.gov/api-spec/fdc_api.html)

## Useage

1. clone this repository

    ```sh
    % git clone https://github.com/jericho1050/calorie-contra.git
    ```

2. create an virtual env

    ```sh
    % virtualenv env
    ```

    or

    ```sh
    % python -m venv env
    ```

    then activate it

    ```sh
    ### MacOS
    % source env/bin/activate
    ```

    ```sh
    ### Windows
    % .\env\Scripts\activate
    ```

3. Install the dependencies

    ```sh
    % pip install -r requirements.txt
    ```

4. Create .env file for api_key and secret variables

    ```sh
    #.env
    api_key = "get_yours_at_usda_fdc"
    SECRET_KEY="your_secret_key_here"
    ```

5. Run the server

    ```bash
    % python app.py
    ```

## Walkthrough of each file

TODO

## Test

TODO

## Contribution Guideline

TODO
