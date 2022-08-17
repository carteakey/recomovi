# Recomovi

Content-based Movie Recommendation App. 
The app can be run here:
[share.streamlit.io/carteakey/recomovi](https://share.streamlit.io/carteakey/recomovi/).

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

