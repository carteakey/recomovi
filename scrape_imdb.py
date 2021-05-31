# handle imports and globals
# from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
# from warnings import warn
import requests
from bs4 import BeautifulSoup, element
import re
import random
import aiohttp
import asyncio
import time
import pandas as pd
import os
from IPython.core.display import clear_output


IMDB_TITLE_URL = "https://www.imdb.com/title/tt"
IMDB_SRCH_URL = "https://www.imdb.com/search/title/?title_type=feature&languages=en"

# https://www.imdb.com/title/tt12361974/plotsummary?


MATCH_ALL = r'.*'


def random_with_N_digits(n):
    """
    Return a random number with specified length.
    """
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return random.randint(range_start, range_end)


def like(string):
    """
    Return a compiled regular expression that matches the given
    string with any prefix and postfix, e.g. if string = "hello",
    the returned regex matches r".*hello.*"
    """
    string_ = string
    if not isinstance(string_, str):
        string_ = str(string_)
    regex = MATCH_ALL + re.escape(string_) + MATCH_ALL
    return re.compile(regex, flags=re.DOTALL)


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


def parse(html):

    data = {}

    # Create a BeautifulSoup object
    soup = BeautifulSoup(html, 'html.parser')

    title = soup.find('title')

    if title.text == '404 Error - IMDb':
        return None

    else:
        # page title
        title = soup.find('h1')

        if title is not None:
            data['title'] = title.text

        rating = soup.find("span", {"class": like(
            'AggregateRatingButton__RatingScore')})
        if rating is not None:
            data['Rating'] = rating.text

        ratingCount = soup.find("span", {"class": like(
            'AggregateRatingButton__TotalRatingAmount')})
        if ratingCount is not None:
            data['ratingCount'] = ratingCount.text

        return data


def parse_search_page(html):

    movie_list = []

    # Parse the content of the request with BeautifulSoup
    page_html = BeautifulSoup(html, 'html.parser')

    # Select all the 50 movie containers from a single page
    mv_containers = page_html.find_all(
        'div', class_='lister-item mode-advanced')

    # For every movie of these 50
    for container in mv_containers:
        # If the movie has a Rating, then:
        if container.strong.text is not None:

            data = {}

            # Scrape the name
            title_id = container.a['href'].split('/')[2]
            data['imdb_title_id'] = title_id

            # Scrape the name
            name = container.h3.a.text
            data['title'] = name

            # Scrape the year
            year = container.h3.find(
                'span', class_='lister-item-year').text.replace('(', '').replace(')', '')
            if ' ' in year:
                year = year.split(' ')[1]
            data['year'] = year

            # Scrape the certificate
            certificate = container.find('span', class_='certificate')
            if certificate is not None:
                data['certificate'] = certificate.text

            # Scrape the genre
            genre = container.find('span', class_='genre').text.strip()
            data['genre'] = genre

            # Scrape the runtime
            runtime = container.find('span', class_='runtime').text
            data['runtime'] = runtime

            # Scrape the description
            description = container.findAll('p', class_='text-muted')
            data['description'] = description[1].text.strip()

            # Scrape the IMDB rating
            imdb = float(container.strong.text)
            data['IMDb_rating'] = imdb

            # Scrape the Metascore
            m_score = container.find('span', class_='metascore')
            if m_score is not None:
                data['MetaScore'] = m_score.text

            # Scrape the number of votes
            vote = container.find('span', attrs={'name': 'nv'})['data-value']
            data['ratingCount'] = vote

            # Scrape the directors and actors

            credit_container = container.find('p', class_="")
            a_tag = credit_container.find('a')

            text = a_tag.previousSibling

            stars = []

            if text.strip() == 'Director:':
                data['directors'] = a_tag.text
                stars = [a.get_text() for a in a_tag.find_next_siblings('a')]

            elif text.strip() == 'Directors:':
                directors = []
                while True:
                    if isinstance(a_tag, element.Tag):
                        if a_tag.name == 'span':
                            break
                        else:
                            # string concatenation
                            directors.append(a_tag.text)
                            a_tag = a_tag.nextSibling
                    else:
                        a_tag = a_tag.nextSibling

                stars = [a.get_text() for a in a_tag.find_next_siblings('a')]

                data['directors'] = ','.join(directors)

            else:
                stars = stars = [a.get_text()
                                 for a in credit_container.find_all('a')]

            data['stars'] = ','.join(stars)

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
        return await asyncio.gather(
            *(fetch_and_parse(session, url) for url in urls)
        )


if __name__ == '__main__': 

    output = pd.DataFrame()
    # 5 pages per year
    pages = [str(i) for i in range(1, 251, 50)]
    years_url = [str(i) for i in range(1990, 2021)]

    try:

        for year_url in tqdm(years_url):

            start_time = time.time()

            data = []
            urls = []
            for page in pages:
                urls.append(IMDB_SRCH_URL+"&release_date=" +
                            year_url + '&sort=num_votes,desc&&start=' + page)

            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy())
            data = asyncio.run(scrape_urls(urls))

            print("\n Scraping Year:"+year_url)
            print(*urls, sep="\n")
            print("--- %s seconds ---" % (time.time() - start_time))
            
            for rec in data:
                output = output.append(rec, ignore_index=True)

            print('Waiting for few seconds')
            time.sleep(random.randint(8, 15))
            clear_output(wait = True)

        
        clear_output(wait = True)
        print('Writing to csv')
        file = 'data.csv'
        if(os.path.exists(file) and os.path.isfile(file)):
            os.remove(file)
            print('removed existing csv file')
        
        output.to_csv('data.csv', encoding="utf8",
                        mode='a', index=False, header=True)
        print('Done....')

    except KeyboardInterrupt:
        print("Execution halted")
        pass
