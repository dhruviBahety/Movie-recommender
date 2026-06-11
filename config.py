import os

# TMDB API
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "8265bd1679663a7ea12ac168da84d2e8")
TMDB_API_BASE_URL = "https://api.themoviedb.org/3/movie"
TMDB_POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"

# Model paths
MOVIE_LIST_PATH = "model/movie_list.pkl"
SIMILARITY_PATH = "model/similarity.pkl"

# Recommendation settings
NUM_RECOMMENDATIONS = 5
