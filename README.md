# desttrack calorie counter
#### Video Demo:  https://www.youtube.com/watch?v%253DrTQ18UzFF-8
#### Description:This calorie counter web app has a login/register feature for individuals who want to track their calories and macros throughout the day and week. For searching data, I used a REST API from the USDA FDC https://fdc.nal.usda.gov/api-spec/fdc_api.html `index.html` The search form returns a list of foods 'results.html' and also a separate list for the BRANDED datatype 'results-branded.html'. You can see nutritional facts for every individual food that the search query returned. If you clicked on one of them, you went to a different route `/details` that lets you modify the serving size according to your needs `result.html`.Then you can add it to your log for it to show in your personal graph of its calories and macros `/food-log` route.In helpers.py is where the retrieving of my data is, from the API.Requesting through different endpoints for my needs.And parsing the data so i can use the relevant part.The `def lookup_nutritional_info(query, api_key)` this function is used by my `/details` where it returns nutritional facts of a food.The `def search_food(query, api_key, page, page_size):` function searches for foods then returns a list based on match query.The `def get_nutritional_info(fdc_ids, api_key):` returns a partial nutritional fact such as calorie and its macros for every food in the list that search returned.These two function is used by `/results` and `/results-branded` route.Where from the templates `results.html` and `results-branded.html` displays the list of foods along with it's calories,protein,carbs and fat for users to see. These two functions are kind of duplicates of those I used for my branded.db because I didn't include the branded datatype in the endpoints. Namely `def get_nutritional_info_branded(fdc_ids, page):` and `def search_food_branded(q)`.As for my branded.db. I downloaded data for branded from https://fdc.nal.usda.gov/download-datasets.html. I then imported two relevant.csv files into my SQL database, 'branded.db, for necessary queries. As for the UI, the color palette I've used is 60% white (Background), 30% green (text), and 10% (buttons) blue. I've also added a spinner loader to the `index.html` while the data is loading or we're requesting it from the API server.


##### Note: Since the BRANDED database is such a large file, I have to download the data and import it into my SQL. That's why it's not updated. Because if we include the branded datatype at our endpoint for fetching or requesting branded data, the web app often takes time to load or crashes.








