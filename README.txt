INSTRUCTIONS:

1. Install Keras and set up with Theano or TensorFlow
2. Get Riot API Key and set the key as `API_KEY` in a file called api_info.py
3. Install PostgreSQL Version 9.3+ (9.5+ recommended). Edit the database connection info in the files as necessary (I will create a new file later to use imports)
4. Adjust the time.sleep(...) statements in get_match_data.py and get_league_data.py, since I was running into strange rate-limiting issues with the API, even though
   I was greatly under the rate-limit
5. Run get_league_data.py in order to start getting some users and their matches.
6. Run get_match_data.py after you've run get_league_data.py to get more complete match information.
7. Run the code in dbcleaning.sql in the database with all the data.
8. You can adjust train_model.py a bit (Keras is very simple) and try running the model. Right now I'm still in the exploratory phase.
