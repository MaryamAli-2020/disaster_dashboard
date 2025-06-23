# 🌍 Real-Time Disaster Relief & Resource Map

## Overview
A real-time dashboard that shows live data on natural disasters (earthquakes, floods, etc.), available shelters, donation centers, and predicted aid needs.

## Features
- 🌍 Live map with disaster data (USGS)
- 🧭 Mock shelter and donation center map
- 📈 Basic ML analysis on historical disasters
- ⚡ FastAPI backend with Streamlit frontend

## Tech Stack
- **Backend**: Python + FastAPI
- **Frontend**: Streamlit (alt: React + Leaflet.js)
- **ML/Analytics**: Pandas, Scikit-learn (notebook)
- **Deployment**: Railway, Render, or localhost

## Quickstart
```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
streamlit run frontend/streamlit_app.py
```

## Disaster APIs Used
- USGS Earthquake: https://earthquake.usgs.gov/fdsnws/event/1/
