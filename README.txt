INSTRUCTIONS:

1. Install Keras and set up with Theano or TensorFlow
2. Get Riot API Key and set the key as `API_KEY` in a file called api_info.py
3. Install PostgreSQL Version 9.3+ (9.5+ recommended). Edit the database connection info in dbinfo.py as necessary 
4*. Adjust the time.sleep(...) statements in get_match_data.py and get_league_data.py
  
5. Run get_league_data.py in order to start getting some users and their matches.
6. Run get_match_data.py after you've run get_league_data.py to get more complete match information.
7. Run assign_match_version.py to insert match version tables into the database.
8. Run insert_static.py to insert updated static champion data into database using the static API (has no rate limit).
9. Run the code in dbcleaning.sql in the database with all the data. The diagnostic code at the end isn't necessary: it just gives you a better idea of what your sample looks like.
10. You can adjust train_model.py a bit (Keras is very simple) and try running the model. Right now I'm still in the exploratory phase.
11. You can run predict_result.py to have it go through a few basic models. You can also import it in another file/Python terminal and make your own predictions.

* get_league_data.py should not give random 429 errors, but I find that is the case with get_match_data.py, even when the returned error header indicates I am well under the rate limit
