# Sports Analytics Assistant

This project ingests sports articles from public RSS feeds, stores embeddings in Qdrant, and answers questions with a Groq model. The FastAPI service combines retrieved passages with optional web search snippets. The Streamlit app provides a simple chat front end that talks to the same API you can call from the interactive docs or any HTTP client.

## Requirements

- Python 3.11
- A Groq API key
- Cloud Qdrant: cluster URL and API key. Local Qdrant can run in Docker with no key.

## Directions

- Open a terminal in the project folder: `sports-analytics-assistant` (or use the full path to this repo on your machine).

- Create a new virtual environment, then install dependencies:
  - `python3.11 -m venv .venv`
  - `source .venv/bin/activate`
  - `pip install -r requirements.txt`

- Copy the environment template and add your keys: `cp .env.example .env` then edit `.env` (see `.env.example` for variable names). Never commit the real `.env` file; it is listed in `.gitignore`.

- Launch a Qdrant cluster in the cloud console, then set `QDRANT_URL` and `QDRANT_API_KEY` in your `.env` file accordingly.

- Ensure a local data directory exists for scraped JSONL (ignored by git): `mkdir -p data`. The ingest code also creates parent directories as needed.

- Load data into the index (scrape RSS, embed, upsert) using either:
  - `python scripts/ingest_qdrant.py --rescrape`, or
  - `POST /ingest` on the API with `{"rescrape": true}` after the server is up.

- Start the API from the project root with the venv active:
  - `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`

- Start the web UI in a second terminal (use the venv’s Streamlit so the correct packages load):
  - `.venv/bin/streamlit run app/streamlit_app.py`

- Open the API browser at `http://127.0.0.1:8000/docs` to try `GET /health`, `POST /ask`, and `POST /ingest` directly.

## API paths

- GET `/health` — check that the service and configuration are visible.
- POST `/ask` — JSON body with `query` and optional `use_web` and `top_k`. Needs `GROQ_API_KEY` in the server environment.
- POST `/ingest` — JSON body with `rescrape` true to scrape first or false to load existing JSONL only.
