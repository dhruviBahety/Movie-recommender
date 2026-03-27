from flask import Flask, render_template, request
import pickle
import requests

app = Flask(__name__)

# ================================
# Load model
# ================================
movies = pickle.load(open('model/movie_list.pkl', 'rb'))
similarity = pickle.load(open('model/similarity.pkl', 'rb'))

# ================================
# Fetch poster
# ================================
def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
        data = requests.get(url).json()
        poster_path = data.get('poster_path')
        return "https://image.tmdb.org/t/p/w500/" + poster_path if poster_path else ""
    except:
        return ""

# ================================
# Recommendation logic
# ================================
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]

    distances = sorted(
        list(enumerate(similarity[index])),
        reverse=True,
        key=lambda x: x[1]
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
    movie_list = movies['title'].values

    if request.method == "POST":
        selected_movie = request.form.get("movie")

        if selected_movie:
            names, posters = recommend(selected_movie)

            return render_template(
                "index.html",
                movies=movie_list,
                selected_movie=selected_movie,
                recommendations=list(zip(names, posters))
            )

    return render_template("index.html", movies=movie_list)

# ================================
# Run
# ================================
if __name__ == "__main__":
    app.run(debug=True)
