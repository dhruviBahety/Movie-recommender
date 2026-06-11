from flask import Flask, render_template, request

from config import MOVIE_LIST_PATH, SIMILARITY_PATH
from utils import get_recommendations, load_pickle

app = Flask(__name__)

movies = load_pickle(MOVIE_LIST_PATH)
similarity = load_pickle(SIMILARITY_PATH)


@app.route("/", methods=["GET", "POST"])
def home():
    movie_list = movies["title"].values
    recommendations = None

    if request.method == "POST":
        selected_movie = request.form.get("movie")
        if selected_movie:
            names, posters = get_recommendations(selected_movie, movies, similarity)
            recommendations = list(zip(names, posters))

            return render_template(
                "index.html",
                movies=movie_list,
                selected_movie=selected_movie,
                recommendations=recommendations,
            )

    return render_template("index.html", movies=movie_list)


if __name__ == "__main__":
    app.run(debug=True)
