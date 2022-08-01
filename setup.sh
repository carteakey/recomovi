mkdir -p ~/.streamlit/
python3 -m nltk.downloader stopwords
python3 -m nltk.downloader punkt
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml