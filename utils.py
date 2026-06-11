import pickle

import requests

from config import (
    NUM_RECOMMENDATIONS,
    TMDB_API_BASE_URL,
    TMDB_API_KEY,
    TMDB_POSTER_BASE_URL,
)


def load_pickle(path):
    """Load a pickled object from the given file path."""
    with open(path, "rb") as f:
        return pickle.load(f)


def fetch_poster(movie_id):
    """Fetch the poster URL for a movie from TMDB."""
    try:
        url = f"{TMDB_API_BASE_URL}/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        data = requests.get(url).json()
        poster_path = data.get("poster_path")
        if poster_path:
            return f"{TMDB_POSTER_BASE_URL}/{poster_path}"
        return ""
    except Exception:
        return ""


def get_recommendations(movie, movies_df, similarity_matrix):
    """Return lists of recommended movie names and poster URLs."""
    index = movies_df[movies_df["title"] == movie].index[0]

    distances = sorted(
        enumerate(similarity_matrix[index]),
        reverse=True,
        key=lambda x: x[1],
    )

    names = []
    posters = []
    for i in distances[1 : NUM_RECOMMENDATIONS + 1]:
        row = movies_df.iloc[i[0]]
        names.append(row.title)
        posters.append(fetch_poster(row.movie_id))

    return names, posters
