# 🌱 EcoPath AI

**A multi-modal navigation engine that optimizes routes for environmental health instead of speed.**

EcoPath AI calculates the "greenest route" — not the fastest one — using real-world environmental data including air quality, road elevation, street canyon geometry, and tree coverage.

---

## 🎯 Core Concept

Instead of "fastest route", EcoPath AI calculates "greenest route" using 5 environmental factors:
```
Eco_Score = (Traffic × W₁) + (AQI × W₂) + (Gradient × W₃) - (Carpool × W₄) - (Greenery × W₅) + (Canyon × W₆)
```

| Factor | Description | Data Source |
|---|---|---|
| 🚗 Traffic Penalty | Congestion = more emissions | OSM speed limits |
| 😷 AQI Penalty | Avoid high-pollution areas | OpenWeatherMap API |
| ⛰️ Gradient Penalty | Steep roads = more fuel consumption | Open-Elevation API |
| 🤝 Carpool Bonus | Sharing vehicles reduces eco-cost | User matching |
| 🌳 Greenery Bonus | Tree coverage reduces eco-cost | OSM canopy data |
| 🏙️ Canyon Penalty | Trap zones where exhaust concentrates | OSM building geometry |

---

## ✅ What's Built

### Core Engine
- **Eco-Cost Heuristic Calculator** — 6-component formula with dynamic weight adjustment
- **Pathfinding Engine** — Dijkstra's + A* algorithm optimizing for eco-cost, not distance
- **Dynamic Weights** — Weights shift automatically based on time of day and AQI levels
  - Morning peak (7-9 AM) → traffic and AQI weighted heavier
  - Evening peak (5-7 PM) → highest penalty period
  - Night (10 PM-6 AM) → gradient weighted heavier, traffic lighter
  - AQI Emergency (>300) → AQI weight boosted regardless of time

### 3 Environmental Models
1. **AQI Model** — Real air quality data from OpenWeatherMap API per route area
2. **Elevation/Gradient Model** — Real road steepness via Open-Elevation API, calculates gradient % per segment
3. **Street Canyon Model** — Detects urban trap zones using OSM building heights and street widths. Street Canyon Index = Building Height / Street Width

### Road Network
- **Global OSM Integration** — Real road data via osmnx for any location worldwide
- **Real speed limits** from OSM maxspeed tags
- **Nearest node lookup** using haversine distance

### API
- `POST /api/v1/routes/calculate` — Main route calculation endpoint
- `GET /api/v1/routes/health` — Health check
- Auto-generated Swagger docs at `/docs`

### Web UI
- Interactive Leaflet.js map with real road-following path
- Waypoint markers at intermediate nodes
- Eco-cost breakdown visualization
- Vehicle type selection (ICE / EV / Hybrid)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation
```bash
git clone https://github.com/graduationlearn-wq/EcoPath-AI
cd ecopath-backend
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the root directory:
```
OPENWEATHER_API_KEY=your_openweathermap_api_key_here
```

Get a free API key at [openweathermap.org](https://openweathermap.org/api)

### Run
```bash
python -m uvicorn app.main:app --reload
```

Open `http://localhost:8000`

---

## 📁 Project Structure
```
ecopath-backend/
├── app/
│   ├── main.py                        # FastAPI app entry
│   ├── config.py                      # Configuration + env vars
│   ├── api/
│   │   ├── routes/
│   │   │   └── routes.py              # API endpoints
│   │   └── schemas/
│   │       └── route_schemas.py       # Pydantic models
│   ├── engines/
│   │   ├── eco_cost.py                # Eco-cost formula engine
│   │   ├── pathfinding.py             # Dijkstra + A* pathfinding
│   │   └── graph_builder.py           # OSM road network builder
│   └── services/
│       ├── route_service.py           # Main business logic
│       ├── aqi_service.py             # OpenWeatherMap AQI
│       ├── elevation_service.py       # Open-Elevation gradients
│       ├── street_canyon_service.py   # Urban canyon detection
│       └── weight_service.py          # Dynamic weight adjustment
├── index.html                         # Web UI
├── requirements.txt                   # Dependencies
└── .env.example                       # Environment template
```

---

## 🔧 Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python |
| Pathfinding | NetworkX, custom A* |
| Road Network | osmnx + OpenStreetMap |
| AQI Data | OpenWeatherMap Air Pollution API |
| Elevation Data | Open-Elevation API |
| Canyon Data | OSM building geometry |
| Frontend | HTML/CSS/JS, Leaflet.js |
| Maps | OpenStreetMap tiles |

---

## ⏳ Roadmap

- [ ] Live traffic API integration
- [ ] Carpool matching engine
- [ ] Multi-modal routing (Park & Walk, Park & Ride)
- [ ] NDVI satellite data for real canopy density
- [ ] PostgreSQL + PostGIS database
- [ ] Redis caching for elevation data
- [ ] User accounts and trip history

---

## 📊 Sample Output
```
Route: 1.18 km · 1 min
Eco-Score: 15.10

🚗 Traffic Penalty    +0.00
😷 AQI Penalty       +50.00
⛰️ Gradient Penalty   +5.21
🤝 Carpool Bonus       0.00
🌳 Greenery Bonus     -5.00
🏙️ Canyon Penalty    +16.75
```

---

## 🔑 API Keys Required

| Service | Purpose | Cost |
|---|---|---|
| [OpenWeatherMap](https://openweathermap.org/api) | Real AQI data | Free tier |
| Open-Elevation | Road gradient data | Free, no key needed |
| OpenStreetMap | Road network | Free, no key needed |

---

*Built with the goal of making every navigation decision an environmental one.*
