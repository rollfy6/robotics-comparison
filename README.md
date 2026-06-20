# Robotics Industry Comparison

Streamlit dashboard for comparing warehouse and logistics robotics companies, products, specifications, and industry relationships.

## Setup

```bash
cd robotics-comparison
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

On first launch, the SQLite database is created and seeded automatically from bundled data.

## Features

- Company and product comparison with specs, capabilities, and news feeds
- Interactive network graph of company associations
- Case study scraping and industry source tracking
- Side-by-side product spec analysis
