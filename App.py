import json
from pathlib import Path
import pickle
import streamlit as st
import requests
import time
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
st.set_page_config(
    page_title="CineAI - Movie Recommender",
    page_icon="🎬",
    layout="centered"
)

# TMDB API Configuration
TMDB_API_KEY = "68fa86877a10fe6349fff68a23f62007"

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
    # File IDs and their destinations
    files = {
        "movie_list.pkl": "1Uhr1m4oEK7X2MpUngWNgTLqyucLJjKzV",
        "similarity.pkl": "1It16hDih8qEXKrCL43a6s8hsxtPpYvIC"
    }

    # Download missing files
    for filename, file_id in files.items():
        if not os.path.exists(filename):
            url = f"https://drive.google.com/uc?id={file_id}"
            gdown.download(url, filename, quiet=False)
            print(f"Downloaded {filename}")

    # Load files
    movies = pickle.load(open('movie_list.pkl', 'rb'))
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    return movies, similarity


# Watchlist functions
def load_watchlist():
    if Path("watchlist.json").exists():
        with open("watchlist.json", "r") as f:
            return json.load(f)
    return []


def save_watchlist(watchlist):
    with open("watchlist.json", "w") as f:
        json.dump(watchlist, f)


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
# ... (keep all your imports and setup code the same until the main() function)

def main():
    movies, similarity = load_data()

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

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎬 Movie Recommender",
        "📊 Sentiment Analysis",
        "💾 My Watchlist",
        "🍿 Trailer Wall"
    ])

    # Handle tab switching
    if st.session_state.current_tab != st.session_state.active_tab:
        st.session_state.active_tab = st.session_state.current_tab
        st.rerun()

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

                    if st.button(f"➕ Add to Watchlist",
                                 key=f"add_{name}",
                                 use_container_width=True):
                        if 'watchlist' not in st.session_state:
                            st.session_state.watchlist = []

                        if name not in [m['name'] for m in st.session_state.watchlist]:
                            st.session_state.watchlist.append({
                                'name': name,
                                'poster': poster,
                                'added_date': time.strftime("%Y-%m-%d"),
                                'watched': False,
                                'trailer_url': get_movie_trailer(name)
                            })
                            save_watchlist(st.session_state.watchlist)
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
