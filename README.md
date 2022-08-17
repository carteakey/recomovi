[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/carteakey/recomovi/)

# Recomovi

Content-based Movie Recommendation App. 

![Demo](/screenshots/recomovi.png)

### Overview
- Configurable scraper for realtime dataset and keyword generation.
- Scrapes IMDb Advanced Search Page using beautifulsoup. (Top 250 movies each for year 1990-2022). Dataset of approx 8000 movies.
- Rake to extract keywords from plot summary.
- Cosine Similarity Index to filter top 10 similar movies.
- Frontend created using Streamlit.

The web scraper can be run from the terminal as well. It will download the data and keywords in the datasets folder.
```bash
python3 -m scrape_imdb
```
![Terminal](/screenshots/terminal.png)

