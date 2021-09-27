from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import streamlit as st
import pandas as pd
import time
import aiohttp
import asyncio
import random
import os

import scrape_imdb as sc
import utils
import omdb

# check if tmp exists, otherwise create it
tmp_dir = Path("/tmp")
tmp_dir.mkdir(parents=True, exist_ok=True)

# globals
HEADERS = {"Accept-Language": "en-US, en;q=0.5"}
CUSTOM_SCRAPE = tmp_dir / "custom_scrape.csv"
CUSTOM_KEYWORDS = tmp_dir / "custom_keywords.csv"
DEFAULT_SCRAPE = os.path.join("datasets", "default_scrape.csv")
DEFAULT_KEYWORDS = os.path.join("datasets", "default_keywords.csv")

# load default dataset on start to cache getCosineSim
def_keywords = pd.read_csv(DEFAULT_KEYWORDS)
def_movies = pd.read_csv(DEFAULT_SCRAPE)
def_indices = pd.Series(def_keywords["title"])

# improves subsequent loading times
@st.cache
def getCosineSim(keywords=def_keywords):
    count = CountVectorizer()
    count_matrix = count.fit_transform(keywords["bagofwords"])
    cosine_sim = cosine_similarity(count_matrix, count_matrix)
    return cosine_sim


# Load default cosine sim
def_cosine_sim = getCosineSim()


def recomovi(
    title, cosine_sim=def_cosine_sim, keywords=def_keywords, indices=def_indices
):
    recommended_movies = []
    idx = indices[indices == title].index[0]
    score_series = pd.Series(cosine_sim[idx]).sort_values(ascending=False)
    top_10_indices = list(score_series.iloc[1:11].index)

    for i in top_10_indices:
        recommended_movies.append(list(keywords["title"])[i])

    return recommended_movies


@st.cache
def convert_df(df):
    return df.to_csv().encode('utf-8')


def generate_grid(title_id_list):

    Titles = []
    Posters = []

    # links = asyncio.run(scrape_urls(posters))

    for title_id in title_id_list:
        data = omdb.getOMDBInfo(title_id)
        print(title_id)
        Titles.append(data['Title'])
        Posters.append(data['Poster'])

    # populate image grid
    col0, col1, col2, col3, col4 = st.columns(5)
    with col0:
        st.image(Posters[0], caption=Titles[0])
    with col1:
        st.image(Posters[1], caption=Titles[1])
    with col2:
        st.image(Posters[2], caption=Titles[2])
    with col3:
        st.image(Posters[3], caption=Titles[3])
    with col4:
        st.image(Posters[4], caption=Titles[4])

    col5, col6, col7, col8, col9 = st.columns(5)
    with col5:
        st.image(Posters[5], caption=Titles[5])
    with col6:
        st.image(Posters[6], caption=Titles[6])
    with col7:
        st.image(Posters[7], caption=Titles[7])
    with col8:
        st.image(Posters[8], caption=Titles[8])
    with col9:
        st.image(Posters[9], caption=Titles[9])


# Start of Streamlit
st.header("Get Data from IMDb")

filters = st.expander('Filters')

movies_year = filters.slider(
    "Year Range (By Release Date)", 1990, 2021, (2000, 2020))

user_rating = filters.slider("User Rating", 0.1, 10.0, (0.1, 10.0), step=0.1)

no_of_movies = filters.slider(
    "Movies Each Year (By Popularity)", 0, 250, 250, step=50)

genres = [
    "Action",
    "Adventure",
    "Animation",
    "Biography",
    "Comedy",
    "Crime",
    "Drama",
    "Family",
    "Fantasy",
    "History",
    "Horror",
    "Music",
    "Mystery",
    "Romance",
    "Sci-Fi",
    "Thriller",
    "War",
    "Western",
]

genre = filters.multiselect("Genre", genres, default=None)

get_button = filters.button("Get", key=None, help=None)

st.header("Get Recommendations")

dataset = st.radio(
    "Dataset",
    ("Default", "Scraped"),
    help="""1) Default - Pre-generated dataset with all the filters expanded. 
    \n 2) Scraped - Dataset generated realtime by adjusting sliders."""
)

if get_button:

    min = movies_year[0]
    max = movies_year[1] + 1

    pages = [str(i) for i in range(1, no_of_movies, 50)]
    years = [i for i in range(min, max)]

    sc.scrape(pages, years, user_rating, genre,
              data_file=CUSTOM_SCRAPE, keywords_file=CUSTOM_KEYWORDS)

else:

    titles = def_movies['title']
    movies = def_movies

    option = st.selectbox(
        "Movie",
        titles,
        help="Select a movie to get similar suggestions",
    )

    if dataset == "Default":
        recommend = recomovi(option)

    if dataset == "Scraped":

        if os.path.exists(CUSTOM_KEYWORDS) and os.path.isfile(CUSTOM_KEYWORDS):

            keywords = pd.read_csv(CUSTOM_KEYWORDS)
            movies = pd.read_csv(CUSTOM_SCRAPE)

            titles = movies["title"]
            indices = pd.Series(keywords["title"])

            cosine_sim = getCosineSim(keywords)

            recommend = recomovi(option, cosine_sim, keywords, indices)

        else:

            st.error("Please Scrape first before using this option!")
            st.stop()

    recommended_movies = movies.query("title in @recommend")

    generate_grid(recommended_movies["imdb_title_id"].tolist())
