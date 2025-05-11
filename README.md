# 🎬 CineAI - Movie Recommender System

**CineAI** is a powerful and interactive movie recommender system built using Python and Streamlit.  
It leverages TMDb data, machine learning, and natural language processing to provide personalized movie recommendations, sentiment-based review analysis, trailers, and a user watchlist all in a sleek interface.

---
## 🖼️ How It Looks
https://github.com/user-attachments/assets/23c2d959-33ec-4c5a-bef5-2d93dac13880 
## ✅ Features

> ### 🔍 Data Preprocessing:
- Merges datasets, handles missing values, and processes movie metadata for modeling.

> ### 🧠 Feature Extraction:
- Converts textual information into numerical vectors using `CountVectorizer`.
- Applies stemming and removes stopwords for clean feature creation.

> ### 🎯 Recommendation Engine:
- Computes cosine similarity between movie vectors.
- Returns top recommended movies based on user selection.

> ### 🌐 Web Interface:
- Built with **Streamlit** for a responsive and interactive UI.
- Displays movie posters using TMDb API.
> ### 🔐 User Authentication
-Login or browse as a guest
> ### 🍿 Trending Movies
-Real-time trending data via TMDB API
> ### 🎬 Trailer Fetcher:
- Uses YouTube API integration to fetch and display trailers for each movie.

> ### 💬 Sentiment Analysis:
- Analyzes reviews using **VADER** sentiment analyzer.
- Displays percentage of positive/negative reviews.

> ### ⭐ Watchlist Manager:
- Lets users create and manage a personal movie watchlist during the session.

---
## Datasets:
- https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata
