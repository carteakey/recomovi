import streamlit as st
import numpy as np
import pandas as pd
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from scrape_imdb import like
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer

IMDB_POSTER_URL = 'https://www.imdb.com/title/{}/mediaindex?refine=poster'
IMDB_URL = 'https://www.imdb.com/'


keywords = pd.read_csv('final.csv')
movies = pd.read_csv('data.csv')
indices = pd.Series(keywords['title'])

count = CountVectorizer()
count_matrix = count.fit_transform(keywords['bagofwords'])
cosine_sim = cosine_similarity(count_matrix, count_matrix)

def getMediaURL(ids):
    urls = []
    for id in ids:
        urls.append(IMDB_POSTER_URL.format(id))
    return urls

def recomovie(title, cosine_sim=cosine_sim):
    recommended_movies = []
    idx = indices[indices == title].index[0]
    score_series = pd.Series(cosine_sim[idx]).sort_values(ascending=False)
    top_10_indices = list(score_series.iloc[1:11].index)

    for i in top_10_indices:
        recommended_movies.append(list(keywords['title'])[i])

    return recommended_movies

#finds the poster tag in the html and returns link
def getIMDbPosterLink(html):

    soup = BeautifulSoup(html, 'html.parser')
    img_link_tag = soup.find('img', {"class": like(
            'MediaViewerImagestyles__PortraitImage')})
            
    if img_link_tag is None:
        img_link_tag = soup.find('img', {"class": like(
            'MediaViewerImagestyles__LandscapeImage')})

    if img_link_tag is not None:   
        img_link = img_link_tag['src']
        return img_link

#finds the first poster in the media gallery and return the media link
def getIMDbMediaLink(html):

    soup = BeautifulSoup(html, 'html.parser')
    media_thumb_element = soup.find('div', class_='media_index_thumb_list')
    media_link_tag = media_thumb_element.find('a')
    media_link = media_link_tag['href']
    return IMDB_URL+media_link

#asynchronous request fetching
async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

#asynchronous fetch and get link calls
async def fetch_and_getlink(session, url):

    loop = asyncio.get_event_loop()
    html = await fetch(session, url)
    html2 = await fetch(session, getIMDbMediaLink(html))
    paras = await loop.run_in_executor(None, getIMDbPosterLink, html2)
    return paras

#asynchronous wrapper to get details of the passed urls
async def scrape_urls(urls):
    headers = {"Accept-Language": "en-US, en;q=0.5"}
    async with aiohttp.ClientSession(headers=headers) as session:
        return await asyncio.gather(
            *(fetch_and_getlink(session, url) for url in urls)
        )

#Start of Streamlit

st.title('Movie Recommender')

option = st.selectbox(
    'Select a movie to get recommendations', movies['title'])

recommended = recomovie(option)

select = movies.query('title in @recommended')
title_ids = getMediaURL(select['imdb_title_id'].tolist())
titles = select['title'].tolist()

print(title_ids)

#initiate policy and run async function
asyncio.set_event_loop_policy(
    asyncio.WindowsSelectorEventLoopPolicy())
links = asyncio.run(scrape_urls(title_ids))

#populate image grid
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
