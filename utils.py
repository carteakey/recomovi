from bs4 import BeautifulSoup
import base64
import os
import re

IMDB_POSTER_URL = "https://www.imdb.com/title/{}/mediaindex?refine=poster"
IMDB_URL = "https://www.imdb.com/"
IMDB_TITLE_URL = "https://www.imdb.com/title/{}"
IMDB_SRCH_URL = "https://www.imdb.com/search/title/?title_type=feature&languages=en"
MATCH_ALL = r".*"


def getMediaURL(ids):
    urls = []
    for id in ids:
        urls.append(IMDB_POSTER_URL.format(id))
    return urls


def getTitleURL(ids):
    urls = []
    for id in ids:
        urls.append(IMDB_TITLE_URL.format(id))
    return urls


def get_table_download_link(df):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(
        csv.encode()
    ).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="dataset.csv">Download dataset</a>'
    return href


# finds the poster tag in the html and returns link
def getIMDbPosterLink(html):

    soup = BeautifulSoup(html, "html.parser")
    img_link_tag = soup.find(
        "img", {"class": like("MediaViewerImagestyles__PortraitImage")}
    )

    if img_link_tag is None:
        img_link_tag = soup.find(
            "img", {"class": like("MediaViewerImagestyles__LandscapeImage")}
        )

    if img_link_tag is not None:
        img_link = img_link_tag["src"]
        return img_link


# finds the first poster in the media gallery and return the media link
def getIMDbMediaLink(html):

    soup = BeautifulSoup(html, "html.parser")
    media_thumb_element = soup.find("div", class_="media_index_thumb_list")
    media_link_tag = media_thumb_element.find("a")
    media_link = media_link_tag["href"]
    return IMDB_URL + media_link


def delete(filename):
    if os.path.exists(filename) and os.path.isfile(filename):
        os.remove(filename)


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


def getSearchURL(year, page, rating, genre):

    url = IMDB_SRCH_URL

    if rating is not None:
        url += "&user_rating=" + str(rating[0]) + "," + str(rating[1])

    if year is not None:
        url += "&release_date=" + str(year)

    url += "&sort=num_votes,desc"

    if page is not None:
        url += "&&start=" + str(page)

    if genre is not None:
        url += '&genres='+','.join(genre)

    return url
