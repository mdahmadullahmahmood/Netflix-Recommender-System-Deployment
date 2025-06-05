import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import bs4 as bs
import urllib.request
import pickle
import requests

# Load sentiment analysis model and vectorizer
clf = pickle.load(open('nlp_model.pkl', 'rb'))
vectorizer = pickle.load(open('tranform.pkl', 'rb'))

# TMDB API key
TMDB_API_KEY = '82e5f5adefc149655379ef74d531a0ce'

def create_similarity():
    data = pd.read_csv('main_data.csv')
    data['movie_title'] = data['movie_title'].str.lower()
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(data['comb'])
    similarity = cosine_similarity(count_matrix)
    return data, similarity

def rcmd(m):
    m = m.lower()
    try:
        data.head()
        similarity.shape
    except:
        data, similarity = create_similarity()
    if m not in data['movie_title'].unique():
        return 'Sorry! Try another movie name'
    else:
        i = data.loc[data['movie_title'] == m].index[0]
        lst = list(enumerate(similarity[i]))
        lst = sorted(lst, key=lambda x: x[1], reverse=True)[1:11]
        return [data['movie_title'][a[0]] for a in lst]

def convert_to_list(my_list):
    my_list = my_list.split('","')
    my_list[0] = my_list[0].replace('["', '')
    my_list[-1] = my_list[-1].replace('"]', '')
    return my_list

def get_suggestions():
    data = pd.read_csv('main_data.csv')
    return list(data['movie_title'].str.capitalize())

app = Flask(__name__)

@app.route("/")
@app.route("/home")
def home():
    suggestions = get_suggestions()
    return render_template('home.html', suggestions=suggestions)

@app.route("/similarity", methods=["POST"])
def similarity():
    data = request.get_json()
    movie = data.get('name')
    if not movie:
        return "No movie name provided", 400
    rc = rcmd(movie)
    if isinstance(rc, str):
        return rc
    else:
        return "---".join(rc)

@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    title = data['title']
    cast_ids = convert_to_list(data['cast_ids'])
    cast_names = convert_to_list(data['cast_names'])
    cast_chars = convert_to_list(data['cast_chars'])
    cast_profiles = convert_to_list(data['cast_profiles'])
    cast_bdays = convert_to_list(data['cast_bdays'])
    cast_bios = convert_to_list(data['cast_bios'])
    cast_places = convert_to_list(data['cast_places'])
    imdb_id = data['imdb_id']
    poster = data['poster']
    genres = data['genres']
    overview = data['overview']
    vote_average = data['rating']
    vote_count = data['vote_count']
    release_date = data['release_date']
    runtime = data['runtime']
    status = data['status']
    rec_movies = convert_to_list(data['rec_movies'])
    rec_posters = convert_to_list(data['rec_posters'])

    for i in range(len(cast_bios)):
        cast_bios[i] = cast_bios[i].replace(r'\n', '\n').replace(r'\"', '\"')

    movie_cards = {rec_posters[i]: rec_movies[i] for i in range(len(rec_posters))}
    casts = {cast_names[i]: [cast_ids[i], cast_chars[i], cast_profiles[i]] for i in range(len(cast_profiles))}
    cast_details = {cast_names[i]: [cast_ids[i], cast_profiles[i], cast_bdays[i], cast_places[i], cast_bios[i]] for i in range(len(cast_places))}

    try:
        sauce = urllib.request.urlopen(f'https://www.imdb.com/title/{imdb_id}/reviews?ref_=tt_ov_rt').read()
        soup = bs.BeautifulSoup(sauce, 'lxml')
        soup_result = soup.find_all("div", {"class": "text show-more__control"})
    except Exception:
        soup_result = []

    reviews_list = []
    reviews_status = []
    for review in soup_result:
        if review.string:
            reviews_list.append(review.string)
            movie_vector = vectorizer.transform([review.string])
            pred = clf.predict(movie_vector)
            reviews_status.append('Good' if pred else 'Bad')

    movie_reviews = {reviews_list[i]: reviews_status[i] for i in range(len(reviews_list))}

    return render_template('recommend.html',
        title=title,
        poster=poster,
        overview=overview,
        vote_average=vote_average,
        vote_count=vote_count,
        release_date=release_date,
        runtime=runtime,
        status=status,
        genres=genres,
        movie_cards=movie_cards,
        reviews=movie_reviews,
        casts=casts,
        cast_details=cast_details
    )

# --- TMDB API routes used in recommend.js ---

@app.route("/search_movie")
def search_movie():
    title = request.args.get('title')
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"
    response = requests.get(url)
    return response.json()

@app.route("/movie_details")
def movie_details():
    movie_id = request.args.get('id')
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    return response.json()

@app.route("/movie_cast")
def movie_cast():
    movie_id = request.args.get('id')
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    data = response.json()
    cast = data.get('cast', [])[:6]
    cast_data = {
        'cast_ids': [str(member['id']) for member in cast],
        'cast_names': [member['name'] for member in cast],
        'cast_chars': [member.get('character', '') for member in cast],
        'cast_profiles': [
            f"https://image.tmdb.org/t/p/original{member['profile_path']}" if member.get('profile_path') else ''
            for member in cast
        ]
    }
    return cast_data

@app.route("/person")
def person():
    person_id = request.args.get('id')
    url = f"https://api.themoviedb.org/3/person/{person_id}?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    return response.json()

@app.route("/poster")
def poster():
    title = request.args.get('title')
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"
    response = requests.get(url)
    return response.json()

if __name__ == '__main__':
    app.run(debug=True)

