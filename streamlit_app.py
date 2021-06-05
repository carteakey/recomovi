# imports
import streamlit as st
import scrape_imdb as sc
import pandas as pd
import time
import aiohttp
import asyncio
import random
import utils
import os

from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer

# globals
HEADERS = {"Accept-Language": "en-US, en;q=0.5"}

tmp_dir = Path('tmp')
tmp_dir.mkdir(parents=True, exist_ok=True)
CUSTOM_SCRAPE = tmp_dir/"custom_scrape.csv"
CUSTOM_KEYWORDS = tmp_dir/"custom_keywords.csv"

DEFAULT_SCRAPE = os.path.join("datasets","default_scrape.csv") 
DEFAULT_KEYWORDS = os.path.join("datasets","default_keywords.csv") 

# load default dataset on start to cache getCosineSim
def_keywords = pd.read_csv(DEFAULT_KEYWORDS)
def_movies = pd.read_csv(DEFAULT_SCRAPE)
def_indices = pd.Series(def_keywords["title"])

# improves subsequent loading times
@st.cache(suppress_st_warning=True)
def getCosineSim(keywords=def_keywords):
    count = CountVectorizer()
    count_matrix = count.fit_transform(keywords["bagofwords"])
    cosine_sim = cosine_similarity(count_matrix, count_matrix)
    return cosine_sim


def_cosine_sim = getCosineSim()


def recomovie(
    title, cosine_sim=def_cosine_sim, keywords=def_keywords, indices=def_indices
):
    recommended_movies = []
    idx = indices[indices == title].index[0]
    score_series = pd.Series(cosine_sim[idx]).sort_values(ascending=False)
    top_10_indices = list(score_series.iloc[1:11].index)

    for i in top_10_indices:
        recommended_movies.append(list(keywords["title"])[i])

    return recommended_movies


# asynchronous request fetching
async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


# asynchronous fetch and get link calls
async def fetch_and_getlink(session, url):

    loop = asyncio.get_event_loop()
    html = await fetch(session, url)
    html2 = await fetch(session, utils.getIMDbMediaLink(html))
    paras = await loop.run_in_executor(None, utils.getIMDbPosterLink, html2)
    return paras


# asynchronous wrapper to get details of the passed urls
async def scrape_urls(urls):

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        return await asyncio.gather(*(fetch_and_getlink(session, url) for url in urls))


def generate_grid(posters,titles):

    # run async function to get posters
    links = asyncio.run(scrape_urls(posters))

    # populate image grid
    col0, col1, col2, col3, col4 = st.beta_columns(5)
    with col0:
        st.image(links[0], caption=titles[0])
    with col1:
        st.image(links[1], caption=titles[1])
    with col2:
        st.image(links[2], caption=titles[2])
    with col3:
        st.image(links[3], caption=titles[3])
    with col4:
        st.image(links[4], caption=titles[4])

    col5, col6, col7, col8, col9 = st.beta_columns(5)
    with col5:
        st.image(links[5], caption=titles[5])
    with col6:
        st.image(links[6], caption=titles[6])
    with col7:
        st.image(links[7], caption=titles[7])
    with col8:
        st.image(links[8], caption=titles[8])
    with col9:
        st.image(links[9], caption=titles[9])

# Start of Streamlit

modes = ["Scrape IMDb", "Get Recommendations"]

st.sidebar.header("Get Data from IMDb")

movies_year = st.sidebar.slider(
    "Year Range (By Release Date)", 1990, 2021, (2000, 2020)
)

user_rating = st.sidebar.slider(
    "User Rating", 0.1, 10.0, (0.1, 10.0), step=0.1
)

no_of_movies = st.sidebar.slider(
    "Movies Each Year (By Popularity)", 0, 250, 250, step=50
)

button = st.sidebar.button("Get", key=None, help=None)

st.sidebar.header("Get Recommendations")

datasets = []

dataset = st.sidebar.radio("Dataset", ("Default", "Scraped"))

if button:

    scrape = pd.DataFrame()

    min = movies_year[0]
    max = movies_year[1] + 1

    pages = [str(i) for i in range(1, no_of_movies, 50)]
    years = [i for i in range(min, max)]

    placeholder = st.empty()
    progress_bar = st.progress(0)

    for year in years:

        percentage = (year - min) / (max - min)
        progress_bar.progress(percentage)

        placeholder.text("Scraping Year: {}".format(str(year)))

        start_time = time.time()
        data = []
        urls = []
        for page in pages:
            urls.append(
                utils.getSearchURL(year,page,user_rating)
            )

        # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        data = asyncio.run(sc.scrape_urls(urls))

        runtime = round(time.time() - start_time, 2)
        placeholder.text("Scraping Year: {} - {} seconds ".format(str(year), runtime))

        for rec in data:
            scrape = scrape.append(rec, ignore_index=True)

        time.sleep(random.randint(8, 15))

        placeholder.empty()

    progress_bar.progress(100)

    scrape.to_csv(CUSTOM_SCRAPE, encoding="utf8", mode="w", index=False, header=True)

    keywords = sc.get_keywords(scrape)

    keywords.to_csv(
        CUSTOM_KEYWORDS, encoding="utf8", mode="w", index=False, header=True
    )

    st.balloons()

    st.write(scrape)
    st.markdown(utils.get_table_download_link(scrape), unsafe_allow_html=True)

else:

    posters = []
    titles = []
    ratings = []
    webpages = []

    if dataset == "Default":

        option = st.sidebar.selectbox(
            "Movie to get recommendations for", def_movies["title"]
        )

        recommended = recomovie(option)

        select = def_movies.query("title in @recommended")
        posters = utils.getMediaURL(select["imdb_title_id"].tolist())
        webpages = utils.getTitleURL(select["imdb_title_id"].tolist())
        titles = select["title"].tolist()
        ratings = select["IMDb_rating"].tolist()

        generate_grid(posters,titles)

    if dataset == "Scraped":
        
        if os.path.exists(CUSTOM_KEYWORDS) and os.path.isfile(CUSTOM_KEYWORDS):
            
            keywords = pd.read_csv(CUSTOM_KEYWORDS)
            movies = pd.read_csv(CUSTOM_SCRAPE)
            indices = pd.Series(keywords["title"])

            cosine_sim = getCosineSim(keywords)

            option = st.sidebar.selectbox(
                "Movie to get recommendations for", movies["title"]
            )

            recommended = recomovie(option, cosine_sim, keywords, indices)

            select = movies.query("title in @recommended")
            posters = utils.getMediaURL(select["imdb_title_id"].tolist())
            webpages = utils.getTitleURL(select["imdb_title_id"].tolist())
            titles = select["title"].tolist()
            ratings = select["IMDb_rating"].tolist()
            generate_grid(posters,titles)

        else : 
            st.error('No Data Generated')
    