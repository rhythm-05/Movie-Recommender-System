# Movie-Recommender-System
This project features a movie recommender system built with Python. It utilizes data from TMDb to recommend movies based on user input.
## How It Looks
![Screenshot 2024-08-02 at 7 30 29 AM](https://github.com/user-attachments/assets/efe4c538-4825-4fe9-9f49-8a39fe20e231)

![Screenshot 2024-08-02 at 4 07 00 PM](https://github.com/user-attachments/assets/74487565-316e-42b5-a341-59abf2c97f34)
## Features
> ## Data Preprocessing:
      Merges datasets, handles missing values, and processes movie features.
>### Feature Extraction:
      Converts text data into numerical features using CountVectorizer and applies stemming.
>### Recommendation Engine:
      Computes movie similarities and provides recommendations based on user input.
>### Web Interface:
      Built with Streamlit for interactive movie recommendations and poster display.

## Setup
1. Install Dependencies:
   ![Screenshot 2024-08-01 at 9 49 27 PM](https://github.com/user-attachments/assets/2a828947-96ea-44f0-976a-38fead5bea5d)
   
2. Download Datasets:
   https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata

## Files
   ### movie_recommender.py: 
         Contains data processing and recommendation logic.
   ### app.py: 
         Streamlit application for user interaction.
   ### movie_dict.pickle: 
         Serialized movie data.
   ### similarity.pickle: 
         Serialized similarity matrix.
