import pickle
import streamlit as st
import requests
import time
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
from pathlib import Path
import hashlib
import uuid
from datetime import datetime
st.set_page_config(
    page_title="CineAI - Movie Recommender",
    page_icon="🎬",
    layout="centered"
)
st.title("🎬CineAI - Movie Recommender")

st.markdown("""
<style>
    /* Smooth tab transitions */
    .stTabs [role="tabpanel"] {
        transition: all 0.3s ease;
    }

    /* Highlight active tab */
    [aria-selected="true"] {
        background-color: #0d6efd !important;
        color: white !important;
    }

    /* Better trailer container */
    .trailer-container iframe {
        min-height: 500px;
        border-radius: 10px;
        margin: 1rem 0;
    }

    /* Button animations */
    button:active {
        transform: scale(0.98);
    }
</style>
""", unsafe_allow_html=True)

# TMDB API Configuration
TMDB_API_KEY = "68fa86877a10fe6349fff68a23f62007"
# ===== USER DATABASE =====
USER_DB_FILE = "user_data.json"

# Load existing users or create new file
if Path(USER_DB_FILE).exists():
    with open(USER_DB_FILE) as f:
        USER_DB = json.load(f)
else:
    USER_DB = {
        "Rhythm": {
            "name": "Rhythm Gaba",
            "password": hashlib.sha256("password123".encode()).hexdigest(),
            "watchlist": [],
            "joined": "2025-10-05"
        },
        "Jake": {
            "name": "Jake Paralta",
            "password": hashlib.sha256("password123".encode()).hexdigest(),
            "watchlist": [],
            "joined": "2024-12-04"
        }
    }
    with open(USER_DB_FILE, 'w') as f:
        json.dump(USER_DB, f)
# Configure session with retry strategy
session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504, 429]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)

# Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()



@st.cache_data
def load_data():
    movies = pickle.load(open('movie_list.pkl', 'rb'))
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    return movies, similarity


# Watchlist functions
def load_watchlist():
    if st.session_state.auth['user'] == "guest":
        return st.session_state.get('guest_watchlist', [])
    return USER_DB[st.session_state.auth['user']].get('watchlist', [])

def save_watchlist(watchlist):
    if st.session_state.auth['user'] == "guest":
        st.session_state.guest_watchlist = watchlist
    else:
        USER_DB[st.session_state.auth['user']]['watchlist'] = watchlist
        with open(USER_DB_FILE, 'w') as f:  # Save to file
            json.dump(USER_DB, f)

def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return "https://image.tmdb.org/t/p/w500/" + data['poster_path'] if data.get('poster_path') else None
    except Exception as e:
        st.warning(f"Couldn't fetch poster for movie ID {movie_id}")
        return None


def get_movie_trailer(movie_name):
    """Finds YouTube trailer link for any movie"""
    try:
        # Step 1: Find movie ID
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
        search_result = session.get(search_url).json()

        if not search_result.get("results"):
            return None

        movie_id = search_result["results"][0]["id"]

        # Step 2: Find trailers
        videos_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}"
        videos_result = session.get(videos_url).json()

        # Step 3: Get first YouTube trailer
        for video in videos_result.get("results", []):
            if video['type'] == 'Trailer' and video['site'] == 'YouTube':
                return f"https://www.youtube.com/watch?v={video['key']}"

        return None
    except Exception as e:
        st.error(f"Error finding trailer: {e}")
        return None


def get_movie_reviews(movie_name):
    """Fetch top 5 reviews for a movie"""
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
    try:
        search_result = session.get(search_url, timeout=10).json()
        if not search_result.get("results"):
            return None

        movie_id = search_result["results"][0]["id"]
        reviews_url = f"https://api.themoviedb.org/3/movie/{movie_id}/reviews?api_key={TMDB_API_KEY}"
        reviews_result = session.get(reviews_url, timeout=10).json()

        if not reviews_result.get("results"):
            return None

        return [review["content"] for review in reviews_result["results"][:5]]
    except Exception as e:
        st.error(f"Error fetching reviews: {str(e)}")
        return None


def analyze_sentiment(reviews):
    """Analyze reviews and return simple verdicts"""
    if not reviews:
        return None

    results = []
    total_score = 0

    for review in reviews:
        score = analyzer.polarity_scores(review)
        total_score += score['compound']
        verdict = "GOOD 😊" if score['compound'] >= 0.05 else "BAD 😠" if score['compound'] <= -0.05 else "NEUTRAL 😐"
        results.append({
            'review': review,
            'verdict': verdict,
            'score': score['compound']
        })

    average_score = total_score / len(reviews)
    overall_verdict = "GOOD 😊" if average_score >= 0.05 else "BAD 😠" if average_score <= -0.05 else "NEUTRAL 😐"

    return {
        'reviews': results,
        'average_score': average_score,
        'overall_verdict': overall_verdict
    }

def get_trending_movies(time_window='day'):
    url = f"https://api.themoviedb.org/3/trending/movie/{time_window}?api_key={TMDB_API_KEY}"
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return response.json().get('results', [])[:5]  # Top 5 trending
    except Exception as e:
        st.error(f"Error fetching trending movies: {e}")
        return []

def recommend(movie, movies, similarity):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []

    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movie_names.append(movies.iloc[i[0]].title)
        time.sleep(0.2)
        poster = fetch_poster(movie_id)
        recommended_movie_posters.append(poster)

    return recommended_movie_names, recommended_movie_posters

# ===== SESSION MANAGEMENT =====
def init_session():
    if 'auth' not in st.session_state:
        st.session_state.auth = {
            'authenticated': False,
            'user': None,
            'token': None,
            'last_active': None
        }

def login(username, password):
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    if username in USER_DB and USER_DB[username]['password'] == hashed_pw:
        st.session_state.auth = {
            'authenticated': True,
            'user': username,
            'token': str(uuid.uuid4()),
            'last_active': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return True
    return False

def logout():
    st.session_state.auth = {
        'authenticated': False,
        'user': None,
        'token': None,
        'last_active': None
    }
def main():
    movies, similarity = load_data()
    if 'auth' not in st.session_state:
        st.session_state.auth = {
            'authenticated': False,
            'user': None,
            'token': None,
            'last_active': None
        }
    # Simple logout button (top-right corner)
    if st.session_state.auth['authenticated']:
        cols = st.columns([4, 1])
        with cols[1]:
            if st.button("🚪 Logout"):
                st.session_state.auth['authenticated'] = False
                st.rerun()

    # Initialize session state variables
    if 'trailer_to_show' not in st.session_state:
        st.session_state.trailer_to_show = None
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "🎬 Movie Recommender"
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "🎬 Movie Recommender"
    if 'selected_movie' not in st.session_state:
        st.session_state.selected_movie = movies['title'].values[0]
    if 'recommendations' not in st.session_state:  # Initialize recommendations
        st.session_state.recommendations = None
    init_session()


    if not st.session_state.auth['authenticated']:

        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:

            with st.container(border=True):
                st.markdown("## 🎬 Welcome to CineAI")


                tab1, tab2 = st.tabs(["Login", "Guest"])

                with tab1:  # Login Tab
                    with st.form("auth_form"):
                        username = st.text_input("Username")
                        password = st.text_input("Password", type="password")

                        if st.form_submit_button("Login", use_container_width=True):
                            if login(username, password):
                                st.rerun()
                            else:
                                st.error("Invalid credentials")

                with tab2:  # Guest Tab
                    if st.button("Explore as Guest", use_container_width=True):
                        st.session_state.auth = {
                            'authenticated': True,
                            'user': "guest",
                            'token': str(uuid.uuid4()),
                            'last_active': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        if 'guest_watchlist' not in st.session_state:
                            st.session_state.guest_watchlist = []
                        st.rerun()

        return
    # Create tabs
    # Update your tabs definition (add "🔥 Trending" as the first tab)
    tab0, tab1, tab2, tab3, tab4 = st.tabs([
        "🔥 Trending",
        "🎬 Movie Recommender",
        "📊 Sentiment Analysis",
        "💾 My Watchlist",
        "🍿 Trailer Wall"
    ])

    # Handle tab switching
    if st.session_state.current_tab != st.session_state.active_tab:
        st.session_state.active_tab = st.session_state.current_tab
        st.rerun()

    with tab0:
        st.header("🔥 Trending This Week")

        time_window = st.radio("Time Window", ["Today", "This Week"],
                               horizontal=True, index=0)

        trending_movies = get_trending_movies('day' if time_window == "Today" else 'week')

        if trending_movies:
            cols = st.columns(5)
            for i, movie in enumerate(trending_movies):
                with cols[i]:
                    # Movie poster
                    poster_url = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie[
                        'poster_path'] else None
                    st.image(poster_url, use_container_width=True)

                    # Movie title as clickable link
                    tmdb_url = f"https://www.themoviedb.org/movie/{movie['id']}"
                    st.markdown(f"[**{movie['title']}**]({tmdb_url})", unsafe_allow_html=True)

                    # Rating and other info
                    st.caption(f"⭐ {movie.get('vote_average', 'N/A')}/10")

                    # "More Info" button that links to TMDB
                    st.markdown(
                        f'<a href="{tmdb_url}" target="_blank" style="display: inline-block; padding: 0.25rem 0.75rem; background-color: #0d6efd; color: white; border-radius: 0.25rem; text-decoration: none;">More Info</a>',
                        unsafe_allow_html=True
                    )
        else:
            st.warning("Couldn't load trending movies. Try again later.")

    with tab1:
        st.header("🍿 Movie Recommender")

        # Create columns for selectbox and randomizer button
        col_select, col_random = st.columns([4, 1])

        with col_select:
            selected_movie = st.selectbox(
                "🔍 Type or select a movie",
                movies['title'].values,
                index=list(movies['title'].values).index(st.session_state.selected_movie),
                key='movie_select'
            )

        # Update selected movie if it changes
        if selected_movie != st.session_state.selected_movie:
            st.session_state.selected_movie = selected_movie
            st.session_state.recommendations = None  # Clear previous recommendations
            st.rerun()

        with col_random:
            st.write("")  # Vertical spacer
            st.write("")  # Vertical spacer
            if st.button("🎲 Surprise Me!",
                         help="Get a random movie recommendation",
                         use_container_width=True):
                filtered_movies = movies[~movies['title'].isin([st.session_state.selected_movie])]
                random_movie = filtered_movies.sample(1).iloc[0]
                st.session_state.selected_movie = random_movie['title']
                st.session_state.recommendations = None  # Clear previous recommendations
                st.rerun()

        if st.button("🚀 Get Recommendations",
                     type="primary",
                     use_container_width=True):
            with st.spinner('Finding similar movies...'):
                recommended_names, recommended_posters = recommend(st.session_state.selected_movie, movies, similarity)

                st.session_state.recommendations = {
                    'names': recommended_names,
                    'posters': recommended_posters,
                    'selected_movie': st.session_state.selected_movie
                }

                st.session_state.reviews = get_movie_reviews(st.session_state.selected_movie)
                if st.session_state.reviews:
                    st.session_state.sentiment = analyze_sentiment(st.session_state.reviews)
                st.rerun()

        if st.session_state.recommendations:
            st.subheader(f"Movies similar to {st.session_state.recommendations['selected_movie']}")

            cols = st.columns(5)
            placeholder_image = "https://via.placeholder.com/150x225?text=No+Poster"

            for i, (name, poster) in enumerate(zip(
                    st.session_state.recommendations['names'],
                    st.session_state.recommendations['posters']
            )):
                with cols[i]:
                    st.image(poster or placeholder_image,
                             caption=name,
                             use_container_width=True)

                    if st.button(f"▶️ Watch Trailer",
                                 key=f"trailer_{name}",
                                 use_container_width=True):
                        st.session_state.trailer_to_show = name
                        st.session_state.current_tab = "🍿 Trailer Wall"
                        st.rerun()

                    if st.button(f"➕ Add to Watchlist", key=f"add_{name}", use_container_width=True):
                        watchlist = load_watchlist()  # Always use the function

                        if not any(movie['name'] == name for movie in watchlist):
                            watchlist.append({
                                'name': name,
                                'poster': poster,
                                'added_date': datetime.now().strftime("%Y-%m-%d"),
                                'watched': False,
                                'trailer_url': get_movie_trailer(name)
                            })
                            save_watchlist(watchlist)  # Save using the function
                            st.success(f"Added {name} to watchlist!")
                            st.rerun()
                        else:
                            st.warning("Already in watchlist")

    with tab2:
        st.header("📊 Sentiment Analysis")

        if 'recommendations' not in st.session_state:
            st.info("Get recommendations first to see sentiment analysis")
        elif 'reviews' in st.session_state and st.session_state.reviews:
            if st.session_state.sentiment:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Average Sentiment Score",
                        f"{st.session_state.sentiment['average_score']:.2f}"
                    )
                with col2:
                    st.metric(
                        "Overall Verdict",
                        st.session_state.sentiment['overall_verdict']
                    )

                st.subheader("💬 Detailed Reviews")
                for i, review in enumerate(st.session_state.sentiment['reviews'], 1):
                    with st.expander(f"Review {i} ({review['verdict']}) - Score: {review['score']:.2f}"):
                        st.write(review['review'])
            else:
                st.warning("No sentiment data available")
        else:
            st.info("No reviews available for this movie")

    with tab3:
        st.header("💾 My Watchlist")

        if 'watchlist' not in st.session_state:
            st.session_state.watchlist = load_watchlist()

        if st.session_state.watchlist:
            st.subheader("Your Movie Collection")

            col1, col2 = st.columns(2)
            with col1:
                show_watched = st.checkbox("Show watched movies", value=True)
            with col2:
                sort_by = st.selectbox("Sort by", ["Recently Added", "A-Z", "Unwatched First"])

            filtered_watchlist = st.session_state.watchlist.copy()
            if not show_watched:
                filtered_watchlist = [m for m in filtered_watchlist if not m['watched']]

            if sort_by == "Recently Added":
                filtered_watchlist.sort(key=lambda x: x['added_date'], reverse=True)
            elif sort_by == "A-Z":
                filtered_watchlist.sort(key=lambda x: x['name'])
            else:
                filtered_watchlist.sort(key=lambda x: x['watched'])

            cols = st.columns(4)
            for i, movie in enumerate(filtered_watchlist):
                with cols[i % 4]:
                    with st.container(border=True):
                        st.image(movie['poster'], use_container_width=True)
                        st.markdown(f"**{movie['name']}**")
                        st.caption(f"Added: {movie['added_date']}")

                        watched_status = st.checkbox(
                            "Watched",
                            value=movie['watched'],
                            key=f"watched_{movie['name']}"
                        )
                        if watched_status != movie['watched']:
                            movie['watched'] = watched_status
                            save_watchlist(st.session_state.watchlist)
                            st.rerun()

                        if st.button("❌ Remove", key=f"remove_{movie['name']}"):
                            st.session_state.watchlist = [m for m in st.session_state.watchlist if
                                                          m['name'] != movie['name']]
                            save_watchlist(st.session_state.watchlist)
                            st.rerun()
        else:
            st.info("Your watchlist is empty. Add some movies to get started!")

    with tab4:
        st.header("🎬 Trailer Wall")

        if st.session_state.trailer_to_show:
            trailer_url = get_movie_trailer(st.session_state.trailer_to_show)
            if trailer_url:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.subheader(f"Now Playing: {st.session_state.trailer_to_show}")
                with col2:
                    if st.button("← Back to All"):
                        st.session_state.trailer_to_show = None
                        st.rerun()

                st.markdown(f"""
                <div class="trailer-container">
                    <iframe width="100%" height="500" 
                            src="{trailer_url.replace('watch?v=', 'embed/')}" 
                            frameborder="0" 
                            allowfullscreen>
                    </iframe>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Trailer not available")
                st.session_state.trailer_to_show = None

        elif st.session_state.get('recommendations') is not None:  # Check if recommendations exist
            st.write("### All Trailers")
            cols = st.columns(3)
            for i, name in enumerate(st.session_state.recommendations['names']):
                with cols[i % 3]:
                    poster = st.session_state.recommendations['posters'][i]
                    st.image(poster, use_container_width=True)

                    if st.button(f"▶️ Play {name[:15]}...",
                                 key=f"wall_{name}",
                                 use_container_width=True):
                        st.session_state.trailer_to_show = name
                        st.rerun()
        else:
            st.info("Get recommendations first to see trailers")

if __name__ == "__main__":
    main()
