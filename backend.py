import logging
import os
import pickle

from flask import Flask, render_template, request
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ================================
# Load model
# ================================
MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")

try:
    with open(os.path.join(MODEL_DIR, "movie_list.pkl"), "rb") as f:
        movies = pickle.load(f)
    with open(os.path.join(MODEL_DIR, "similarity.pkl"), "rb") as f:
        similarity = pickle.load(f)
    logger.info("Model files loaded successfully.")
except FileNotFoundError as exc:
    logger.critical("Model file not found: %s. The app cannot serve requests.", exc)
    raise SystemExit(
        f"Missing model file: {exc}. Place the required .pkl files in '{MODEL_DIR}'."
    ) from exc
except (pickle.UnpicklingError, EOFError, ValueError) as exc:
    logger.critical("Model file is corrupt or unreadable: %s", exc)
    raise SystemExit(f"Corrupt model file: {exc}") from exc

TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "8265bd1679663a7ea12ac168da84d2e8")
POSTER_REQUEST_TIMEOUT = 5  # seconds

# ================================
# Fetch poster
# ================================
def fetch_poster(movie_id):
    url = (
        f"https://api.themoviedb.org/3/movie/{movie_id}"
        f"?api_key={TMDB_API_KEY}&language=en-US"
    )
    try:
        response = requests.get(url, timeout=POSTER_REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.ConnectionError:
        logger.error("Network error while fetching poster for movie %s", movie_id)
        return ""
    except requests.Timeout:
        logger.error("Timeout while fetching poster for movie %s", movie_id)
        return ""
    except requests.HTTPError:
        logger.error(
            "TMDB API returned %s for movie %s", response.status_code, movie_id
        )
        return ""
    except requests.RequestException as exc:
        logger.error("Unexpected request error for movie %s: %s", movie_id, exc)
        return ""

    poster_path = data.get("poster_path")
    if not poster_path:
        logger.warning("No poster path in TMDB response for movie %s", movie_id)
        return ""
    return f"https://image.tmdb.org/t/p/w500/{poster_path}"


# ================================
# Recommendation logic
# ================================
def recommend(movie):
    matches = movies[movies["title"] == movie].index
    if matches.empty:
        raise ValueError(f"Movie not found in dataset: {movie!r}")

    index = matches[0]

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
        selected_movie = request.form.get("movie")

        if selected_movie:
            try:
                names, posters = recommend(selected_movie)
            except ValueError:
                logger.warning("User submitted unknown movie: %s", selected_movie)
                return render_template(
                    "index.html",
                    movies=movie_list,
                    error=f"Movie '{selected_movie}' was not found in our database.",
                )
            except Exception:
                logger.exception("Unexpected error generating recommendations")
                return render_template(
                    "index.html",
                    movies=movie_list,
                    error="Something went wrong while generating recommendations. Please try again.",
                )

            return render_template(
                "index.html",
                movies=movie_list,
                selected_movie=selected_movie,
                recommendations=list(zip(names, posters)),
            )

    return render_template("index.html", movies=movie_list)


@app.errorhandler(500)
def internal_error(error):
    logger.exception("Internal server error: %s", error)
    return render_template("index.html", movies=[], error="Internal server error."), 500


# ================================
# Run
# ================================
if __name__ == "__main__":
    app.run(debug=True)
