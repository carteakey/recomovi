# imports
from bs4 import BeautifulSoup, element
from tqdm import tqdm
from rake_nltk import Rake
import random
import aiohttp
import asyncio
import time
import pandas as pd
import utils
import streamlit as st
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# globals
IMDB_TITLE_URL = "https://www.imdb.com/title/tt"
IMDB_SRCH_URL = "https://www.imdb.com/search/title/?title_type=feature&languages=en"

DEFAULT_SCRAPE = "datasets/default_scrape.csv"
DEFAULT_KEYWORDS = "datasets/default_keywords.csv"

@st.cache
def convert_df(df):
   return df.to_csv().encode('utf-8')


async def fetch(session, url):
    """
    Get Response from Server
    """
    async with session.get(url) as response:
        return await response.text()


def parse_search_page(html):

    movie_list = []

    # Parse the content of the request with BeautifulSoup
    page_html = BeautifulSoup(html, "html.parser")

    # Select all the 50 movie containers from a single page
    mv_containers = page_html.find_all(
        "div", class_="lister-item mode-advanced")

    # For every movie of these 50
    for container in mv_containers:

        # If the movie has a Rating, then:
        if container.strong.text is not None:

            data = {}

            # Scrape the name
            title_id = container.a["href"].split("/")[2]
            data["imdb_title_id"] = title_id

            # Scrape the name
            name = container.h3.a.text
            data["title"] = name

            # Scrape the year
            year = (
                container.h3.find("span", class_="lister-item-year")
                .text.replace("(", "")
                .replace(")", "")
            )
            if " " in year:
                year = year.split(" ")[1]
            data["year"] = year

            # Scrape the certificate
            certificate = container.find("span", class_="certificate")
            if certificate is not None:
                data["certificate"] = certificate.text

            # Scrape the genre
            genre = container.find("span", class_="genre")
            if genre is not None:
                data["genre"] = genre.text.strip()

            # Scrape the runtime
            runtime = container.find("span", class_="runtime")
            if runtime is not None:
                data["runtime"] = runtime.text

            # Scrape the description
            description = container.findAll("p", class_="text-muted")
            if description is not None:
                data["description"] = description[1].text.strip()

            # Scrape the IMDB rating
            imdb = float(container.strong.text)
            data["IMDb_rating"] = imdb

            # Scrape the Metascore
            m_score = container.find("span", class_="metascore")
            if m_score is not None:
                data["MetaScore"] = m_score.text

            # Scrape the number of votes
            vote = container.find("span", attrs={"name": "nv"})["data-value"]
            data["ratingCount"] = vote

            try:
                # Scrape the directors and actors, bit wonky
                credit_container = container.find("p", class_="")
                a_tag = credit_container.find("a")

                text = a_tag.previousSibling

                stars = []

                if text.strip() == "Director:":
                    data["directors"] = a_tag.text
                    stars = [a.get_text()
                             for a in a_tag.find_next_siblings("a")]

                elif text.strip() == "Directors:":
                    directors = []
                    while True:
                        if isinstance(a_tag, element.Tag):
                            if a_tag.name == "span":
                                break
                            else:
                                # string concatenation
                                directors.append(a_tag.text)
                                a_tag = a_tag.nextSibling
                        else:
                            a_tag = a_tag.nextSibling

                    stars = [a.get_text()
                             for a in a_tag.find_next_siblings("a")]

                    data["directors"] = ",".join(directors)

                else:
                    stars = [
                        a.get_text() for a in credit_container.find_all("a")
                    ]

                data["stars"] = ",".join(stars)

            except AttributeError:
                pass
            # append to list
            movie_list.append(data)

    return movie_list


async def fetch_and_parse(session, url):

    html = await fetch(session, url)
    loop = asyncio.get_event_loop()

    # run parse(html) in a separate thread, and
    # resume this coroutine when it completes
    paras = await loop.run_in_executor(None, parse_search_page, html)
    return paras


async def scrape_urls(urls):

    headers = {"Accept-Language": "en-US, en;q=0.5"}
    async with aiohttp.ClientSession(headers=headers) as session:
        return await asyncio.gather(*(fetch_and_parse(session, url) for url in urls))


def rake_implement(x, r):

    r.extract_keywords_from_text(x)
    return r.get_ranked_phrases()


def get_keywords(df_scrape):

    # Make a copy of the passed dataframe
    df = df_scrape.copy()
    df["stars"].fillna("", inplace=True)
    df["directors"].fillna("", inplace=True)
    df["genre"].fillna("", inplace=True)

    # initialize Rake
    r = Rake()

    # Extract keywords
    df["keywords"] = df["description"].apply(lambda x: rake_implement(x, r))

    df["genre"] = df["genre"].map(lambda x: x.split(","))

    df["stars"] = df["stars"].map(lambda x: x.split(","))

    df["directors"] = df["directors"].map(lambda x: x.split(","))

    for index, row in df.iterrows():
        df.at[index, "genre"] = [x.lower().replace(" ", "")
                                 for x in row["genre"]]

        df.at[index, "stars"] = [x.lower().replace(" ", "")
                                 for x in row["stars"]]

        df.at[index, "directors"] = [
            x.lower().replace(" ", "") for x in row["directors"]
        ]

    df["bagofwords"] = ""

    # mentioning 'genre', 'directors', 'stars' multiple times to increase weight, personal preference

    columns = ["genre", "directors", "stars",
               "genre", "directors", "stars", "keywords"]
    for index, row in df.iterrows():
        words = ""
        for col in columns:
            words += " ".join(row[col]) + " "
        df.at[index, "bagofwords"] = words

    df = df[["title", "bagofwords"]]

    return df


def scrape(pages, years, user_rating, genre, data_file=DEFAULT_SCRAPE, keywords_file=DEFAULT_KEYWORDS):

    scrape = pd.DataFrame()

    placeholder = st.empty()
    progress_bar = st.progress(0)

    try:

        # Loop through years
        for year in tqdm(years):
            
            data = []
            urls = []

            # show progress
            start_time = time.time()
            percentage = (year - years[0]) / (years[-1]+1 - years[0])
            progress_bar.progress(percentage)
            placeholder.text("Scraping Year: {}".format(str(year)))

            for page in pages:
                urls.append(utils.getSearchURL(year, page, user_rating, genre))

            # Asynchronously get data from server
            data = asyncio.run(scrape_urls(urls))

            # Append response to dataframe
            for rec in data:
                scrape = scrape.append(rec, ignore_index=True)
                # print(rec)
            # Waiting randomly to not overload server and get banned :)
            time.sleep(random.randint(7,10))
            
            #check runtime
            runtime = round(time.time() - start_time, 2)
            print("\n Scraping Year:" + str(year))
            print(*urls, sep="\n")
            print("--- %s seconds ---" % (runtime))
            placeholder.text("Scraping Year: {}".format(str(year)))
            placeholder.empty()

        utils.delete(data_file)
        utils.delete(keywords_file)

        scrape.to_csv(
            data_file, encoding="utf8", mode="a", index=False, header=True
        )

        keywords = get_keywords(scrape)

        keywords.to_csv(
            keywords_file, encoding="utf8", mode="a", index=False, header=True
        )

        csv = convert_df(scrape)
        st.download_button('Download data as CSV', csv, file_name='imdb_dataset.csv',
                           mime=None, key=None, help=None, on_click=None, args=None, kwargs=None)

        progress_bar.progress(100)
        st.balloons()
        st.write(scrape)

        print("Done....")

    except KeyboardInterrupt:
        print("Execution halted")
        pass


if __name__ == "__main__":

    pages = [i for i in range(1, 251, 50)]
    years = [i for i in range(1990, 2022)]

    scrape(pages, years, None, None)
