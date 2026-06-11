import logging
import os

from flask import Flask, render_template, request
import requests

app = Flask(__name__)

TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
if not TMDB_API_KEY:
    logging.warning(
        "TMDB_API_KEY is not set. Poster fetching will be disabled."
    )

REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "5"))


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# ================================
# Load model
# ================================
try:
    import pickle  # noqa: S403 — pickle is required for the pre-built model files

    with open("model/movie_list.pkl", "rb") as f:
        movies = pickle.load(f)  # noqa: S301
    with open("model/similarity.pkl", "rb") as f:
        similarity = pickle.load(f)  # noqa: S301
except FileNotFoundError:
    logging.error(
        "Model files not found. Place movie_list.pkl and similarity.pkl in model/."
    )
    raise

# ================================
# Fetch poster
# ================================
def fetch_poster(movie_id):
    if not TMDB_API_KEY:
        return ""
    try:
        url = (
            f"https://api.themoviedb.org/3/movie/{movie_id}"
            f"?api_key={TMDB_API_KEY}&language=en-US"
        )
        data = requests.get(url, timeout=REQUEST_TIMEOUT).json()
        poster_path = data.get("poster_path")
        return (
            "https://image.tmdb.org/t/p/w500/" + poster_path
            if poster_path
            else ""
        )
    except (requests.RequestException, ValueError, KeyError):
        return ""

# ================================
# Recommendation logic
# ================================
def recommend(movie):
    matches = movies[movies["title"] == movie]
    if matches.empty:
        return [], []

    index = matches.index[0]

    distances = sorted(
        list(enumerate(similarity[index])),
        reverse=True,
        key=lambda x: x[1],
    )

    names = []
    posters = []

    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id
        names.append(movies.iloc[i[0]].title)
        posters.append(fetch_poster(movie_id))

    return names, posters

# ================================
# Routes
# ================================
@app.route("/", methods=["GET", "POST"])
def home():
    movie_list = movies["title"].values

    if request.method == "POST":
        selected_movie = request.form.get("movie", "")

        if selected_movie and selected_movie in movie_list:
            names, posters = recommend(selected_movie)

            return render_template(
                "index.html",
                movies=movie_list,
                selected_movie=selected_movie,
                recommendations=list(zip(names, posters)),
            )

    return render_template("index.html", movies=movie_list)

# ================================
# Run
# ================================
if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
