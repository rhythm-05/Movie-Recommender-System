import pickle
import streamlit as st
import pandas as pd
import requests


def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=68fa86877a10fe6349fff68a23f62007&language=en-US"
    response = requests.get(url)
    data = response.json()
    print(data)  # Debug: Print the API response to check its structure

    # Check if 'poster_path' exists and is not None
    if data.get('poster_path'):
        poster_path = data['poster_path']
        full_path = f"https://image.tmdb.org/t/p/w500/{poster_path}"
        return full_path
    else:
        # Return a placeholder image URL if no poster is available
        return "https://via.placeholder.com/500x750?text=No+Image+Available"


def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_movies_posters = []
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_movies_posters.append(fetch_poster(movie_id))
    return recommended_movies, recommended_movies_posters


# Load movie data and similarity matrix
movies_list = pickle.load(open("movie_dict.pickle", 'rb'))
movies = pd.DataFrame(movies_list)
similarity = pickle.load(open("similarity.pickle", 'rb'))

st.title("🎬 Movie Recommender System")
st.write("Discover movies you'll love based on what you've watched. Select a movie to get started!")

# Movie selection from dropdown
selected_movie_name = st.selectbox(
    "Please select the movie for which you want recommendations",
    movies['title'].values
)
st.markdown(
    """
    <style>
    .main {
        background-color: #1e1e1e;
        color: #ffffff;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    h1, h2, h3, h4, h5, h6, p {
        color: #ffffff;
    }
    .stSelectbox label, .stButton button {
        color: #ffffff;
    }
    .stButton>button {
        background-color: #444444;
        color: white;
        border: 1px solid #555;
        border-radius: 5px;
        padding: 10px;
    }
    .stButton>button:hover {
        background-color: #555555;
        color: #ffffff;
        border: 1px solid #666;
    }
    .stTextArea>div>div>textarea, .stTextInput>div>div>input {
        color: white;
        background-color: #333333;
        border: 1px solid #555;
        border-radius: 5px;
    }
    .css-1cpxqw2, .css-16huue1 {
        background-color: #2e2e2e;
        border: 1px solid #444;
    }
    .stMarkdown {
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Button to show recommendations
if st.button("Recommend"):
    recommended_movies, recommended_movie_poster = recommend(selected_movie_name)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.header(recommended_movies[0])
        st.image(recommended_movie_poster[0])

    with col2:
        st.header(recommended_movies[1])
        st.image(recommended_movie_poster[1])

    with col3:
        st.header(recommended_movies[2])
        st.image(recommended_movie_poster[2])

    with col4:
        st.header(recommended_movies[3])
        st.image(recommended_movie_poster[3])

    with col5:
        st.header(recommended_movies[4])
        st.image(recommended_movie_poster[4])
