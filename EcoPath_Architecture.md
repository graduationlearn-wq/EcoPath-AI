# EcoPath AI: System Architecture Document

**Project:** EcoPath AI - Environmental Health Navigation Engine  
**Version:** 1.0  
**Last Updated:** March 2026  
**Status:** Pre-Development Architecture

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Core Components](#core-components)
4. [Data Architecture](#data-architecture)
5. [API Specification](#api-specification)
6. [Algorithm & Heuristic Design](#algorithm--heuristic-design)
7. [Technology Stack](#technology-stack)
8. [Data Flow Diagrams](#data-flow-diagrams)
9. [Deployment Strategy](#deployment-strategy)
10. [Scalability & Performance Considerations](#scalability--performance-considerations)

---

## Executive Summary

EcoPath AI is a multi-modal navigation engine that optimizes routes for **environmental health and carbon minimization** rather than travel speed. Unlike traditional navigation apps (Google Maps, Apple Maps), EcoPath routes users through:
- Areas with high green canopy density (natural air filtration)
- Roads with minimal gradient (lower emissions)
- Streets with good air circulation (avoiding "trap zones")
- Carpool opportunities that reduce total vehicles in congested areas
- Multi-modal transitions (Park & Walk, Park & Ride) to avoid high-pollution zones

**Target Market:** Indian metropolitan areas (Delhi, Mumbai, Bangalore, Hyderabad, etc.)

**Key Differentiator:** Carpooling and multi-modal routing are not optional features—they are active interventions triggered by the routing engine itself.

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                      │
│  (Mobile App / Web Dashboard / Voice Interface)              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY & ORCHESTRATION               │
│  (Route Request Handler, Authentication, Rate Limiting)     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  CORE ROUTING ENGINE                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Eco-Cost     │  │ Graph-Based  │  │ Multi-Modal  │      │
│  │ Heuristic    │  │ Path-Finding │  │ Transition   │      │
│  │ Calculator   │  │ (Dijkstra+)  │  │ Logic        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Carpool      │  │ Dynamic      │  │ Real-time    │      │
│  │ Matching     │  │ Weight       │  │ AQI Adapter  │      │
│  │ Engine       │  │ Adjuster     │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                 MODEL-STACK PROCESSORS                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Greenery     │  │ Physics      │  │ Urban        │      │
│  │ Detection    │  │ Engine       │  │ Geometry     │      │
│  │ (CV/Sat)     │  │ (Topo)       │  │ (Spatial AI) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                   DATA INTEGRATION LAYER                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Real-time    │  │ Satellite    │  │ Traffic      │      │
│  │ AQI Feeds    │  │ Imagery      │  │ Data         │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Elevation    │  │ Building     │  │ Metro/Public │      │
│  │ Data (DEM)   │  │ Height Maps  │  │ Transit APIs │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                  DATABASE LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Route Cache  │  │ User Profiles │  │ Trip History │      │
│  │ (Redis)      │  │ (PostgreSQL)  │  │ (PostgreSQL) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. API Gateway & Orchestration Layer

**Purpose:** Single entry point for all client requests; handles auth, rate limiting, request validation.

**Key Endpoints:**
- `POST /api/v1/routes/calculate` — Core route calculation
- `GET /api/v1/routes/{routeId}/details` — Detailed route breakdown
- `POST /api/v1/carpool/match` — Carpool matching trigger
- `GET /api/v1/aqi/status` — Current AQI status by region
- `POST /api/v1/feedback/trip` — User feedback on route (for training)
- `GET /api/v1/user/profile` — User preferences & history

**Implementation:** FastAPI (Python) or Express.js + Node.js

---

### 2. Core Routing Engine

#### 2.1 Eco-Cost Heuristic Calculator

**Responsibility:** Compute the eco-cost score for any candidate route.

**Formula:**
```
Eco_Score = (Traffic × W₁) + (AQI × W₂) + (Gradient × W₃) 
            - (Carpool × W₄) - (Greenery × W₅)
```

**Component Breakdown:**

| Component | Input | Output | Calculation |
|-----------|-------|--------|-------------|
| **Traffic** | Current congestion on segment | Traffic penalty (0-100) | Average speed vs. free-flow speed; higher congestion = higher penalty |
| **AQI** | Real-time AQI values (µg/m³) | AQI penalty (0-100) | Normalize AQI readings; apply exponential weighting for hazardous levels |
| **Gradient** | Elevation change / distance | Gradient penalty (0-100) | Steep grades (>5%) trigger exponential CO2 penalty for ICE vehicles |
| **Carpool** | Number of available carpool matches | Carpool bonus (-20 to 0) | Reduces eco-cost if carpool option exists |
| **Greenery** | Green canopy density (%) | Greenery bonus (-20 to 0) | Higher tree coverage = lower eco-cost |

**Dynamic Weighting Logic:**

```python
# Pseudocode for weight adjustment
def adjust_weights(time_of_day, weather, aqi_level, day_type):
    W1_traffic = 0.3 * (1.5 if peak_hour else 0.8)
    W2_aqi = 0.4 * (2.0 if aqi_emergency else 1.0)
    W3_gradient = 0.2 * (1.2 if evening_commute else 0.7)
    W4_carpool = 0.1 * (1.5 if congestion_high else 0.8)
    W5_greenery = 0.15 * (1.3 if summer_heat_wave else 0.9)
    
    # Normalize weights to sum = 1.0
    weights = normalize([W1_traffic, W2_aqi, W3_gradient, W4_carpool, W5_greenery])
    return weights
```

**Parameters to Adjust:**
- Time of day (peak hours vs. off-peak)
- Weather conditions (monsoon, heat wave, dust storm)
- AQI alerts (Red Zone, Orange Zone, etc.)
- Day type (weekday vs. weekend)
- Vehicle type (EV vs. ICE)

---

#### 2.2 Graph-Based Pathfinding Engine

**Responsibility:** Find the global minimum eco-cost path from origin to destination.

**Algorithm:** Modified Dijkstra's + A* heuristic

**Key Features:**
- **Weighted edges:** Each road segment has multiple cost functions (not just distance)
- **Dynamic edge weights:** Weights change based on real-time traffic and AQI
- **Constraint handling:** Can enforce "no gradients > 10%" or "avoid AQI > 400" constraints
- **K-best paths:** Return top 3 eco-optimal routes for user choice

**Pseudocode:**
```python
def find_eco_optimal_route(origin, destination, constraints):
    graph = build_road_graph(bounds)  # Load from OSM + elevation data
    
    for each_edge in graph.edges:
        edge.cost = calculate_eco_cost(
            traffic=get_real_time_traffic(edge),
            aqi=get_aqi_for_location(edge.midpoint),
            gradient=get_elevation_gradient(edge),
            greenery=get_canopy_density(edge),
            weights=get_dynamic_weights()
        )
    
    route = dijkstra_with_astar(
        graph=graph,
        start=origin,
        goal=destination,
        heuristic=euclidean_distance,
        constraints=constraints
    )
    
    return route
```

**Data Structures:**
- Road network graph (nodes = intersections, edges = road segments)
- Node attributes: latitude, longitude, elevation
- Edge attributes: distance, speed_limit, current_traffic, canopy_density, gradient, aqi_zone

---

#### 2.3 Multi-Modal Transition Logic

**Responsibility:** Detect hazardous destination zones and suggest alternatives.

**Decision Tree:**

```
IF destination_aqi > 400 (Hazardous):
    IF distance_to_green_area < 1km:
        Suggest "Park & Walk"
        └─ Recommend parking lot outside hazard zone
    ELSE IF nearest_metro_station < 2km:
        Suggest "Park & Ride"
        └─ Calculate route to station + transit time to destination
    ELSE:
        Suggest "Carpool to reduce per-capita exposure"
        └─ Trigger aggressive carpool matching
```

**Output:** Multi-modal journey object with:
- Primary route (driving portion)
- Transition point (parking location, metro station)
- Secondary route (walking, transit, etc.)
- Time breakdown (driving + walking + waiting)
- Eco-cost comparison vs. direct drive

---

#### 2.4 Carpool Matching Engine

**Responsibility:** Real-time spatial matching of solo drivers with commuters on similar routes.

**Matching Algorithm:**

```python
def find_carpool_matches(driver_origin, driver_destination, departure_time):
    # Query active riders in the system
    candidate_riders = query_riders(
        origin_radius=500m,
        destination_radius=500m,
        time_window=±10_minutes,
        status="waiting_for_match"
    )
    
    matches = []
    for rider in candidate_riders:
        # Calculate route overlap (% of shared path)
        shared_distance = calculate_overlap(
            driver_route=driver_route,
            rider_route=rider_route
        )
        
        if shared_distance > 0.6 * driver_route_length:  # 60% overlap threshold
            match_score = (
                (shared_distance / driver_route_length) * 0.5 +
                (abs(departure_time - rider_departure_time) / 10_min) * 0.3 +
                (rating_of_rider / 5.0) * 0.2
            )
            matches.append({
                'rider_id': rider.id,
                'score': match_score,
                'shared_distance': shared_distance,
                'time_delta': departure_time - rider_departure_time
            })
    
    # Return top 3 matches
    return sorted(matches, key=lambda x: x['score'], reverse=True)[:3]
```

**Carpool Trigger Conditions:**
- Route passes through "Red Zone" (congestion > 70%, AQI > 300)
- Time savings from carpool > 5 minutes
- Rating of matched riders > 4.0 stars

**User Notification:** Real-time push notification with match details and acceptance prompt

---

### 3. Model-Stack Processors

#### 3.1 Greenery Detection Model

**Input:** Satellite imagery (Sentinel-2, Planet Labs) or street-view images

**Output:** Green Canopy Density map for each road segment (0-100%)

**ML Architecture:**
- Pre-trained CNN (ResNet50 or MobileNet) fine-tuned on tree detection
- Semantic segmentation to classify pixels as "vegetation" vs. "non-vegetation"
- Calculate density as: `(vegetation_pixels / total_pixels) * 100`

**Data Sources:**
- USGS/ESA satellite imagery (free, updated monthly)
- Google Street View API (for street-level validation)
- Local tree census data (if available from municipal authorities)

**Processing Pipeline:**
1. Fetch satellite tile for road segment
2. Apply segmentation model
3. Cache result (updates monthly with new satellite pass)
4. Validate with occasional street-view spot checks

**Challenge:** Seasonal changes (monsoon = denser, dry season = sparse)
**Solution:** Use 12-month rolling average to smooth seasonal variance

---

#### 3.2 Physics-Engine Model (Topographical Analytics)

**Input:** Digital Elevation Model (DEM) data, road geometry

**Output:** Road Gradient penalty for each segment

**Calculation:**

```python
def calculate_gradient_penalty(elevation_start, elevation_end, distance):
    elevation_change = abs(elevation_end - elevation_start)
    gradient_percent = (elevation_change / distance) * 100
    
    # CO2 emission multiplier based on gradient
    # Baseline: 1.0x at 0% gradient
    if gradient_percent <= 2:
        co2_multiplier = 1.0
    elif gradient_percent <= 5:
        co2_multiplier = 1.5  # 50% more emissions
    elif gradient_percent <= 8:
        co2_multiplier = 2.5  # 150% more emissions
    else:
        co2_multiplier = 4.0  # 300% more emissions (steep grade)
    
    # Penalty score: 0-100
    penalty = min(gradient_percent * 5 * co2_multiplier, 100)
    return penalty
```

**Data Source:** SRTM 30m DEM or GEBCO for bathymetric data (free, global coverage)

**Processing:**
1. Fetch elevation for origin and destination of each road segment
2. Calculate gradient percentage
3. Apply CO2 multiplier
4. Cache results (static, no updates needed)

---

#### 3.3 Urban Geometry Model (Spatial AI)

**Input:** Building height maps, street network, wind flow data

**Output:** "Street Canyon Index" classification (0-100, where 100 = worst air circulation)

**Street Canyon Formula:**

```python
def calculate_street_canyon_index(street_width, building_height_left, building_height_right, wind_speed):
    # Aspect ratio: height / width
    aspect_ratio = (building_height_left + building_height_right) / (2 * street_width)
    
    # Wind circulation penalty: narrow streets with tall buildings trap air
    wind_penalty = max(0, 1 - (wind_speed / 5.0))  # High wind = low penalty
    
    # Canyon index: combines geometry + wind
    canyon_index = (aspect_ratio * 50) + (wind_penalty * 50)
    
    # Classify as "Trap Zone" if index > 70
    is_trap_zone = canyon_index > 70
    
    return {
        'canyon_index': canyon_index,
        'is_trap_zone': is_trap_zone,
        'aspect_ratio': aspect_ratio,
        'wind_efficiency': 1 - wind_penalty
    }
```

**Data Sources:**
- Open Street Map (building polygons, street geometry)
- SRTM or Google Building Heights API (building heights)
- Weather API (wind speed, direction)

**Processing Pipeline:**
1. Fetch OSM building data for road segment vicinity
2. Get mean building heights
3. Query wind data from weather API
4. Calculate canyon index
5. Flag trap zones for eco-cost penalty

---

### 4. Data Integration Layer

**Purpose:** Aggregate real-time and historical data from multiple sources.

#### 4.1 Real-time AQI Feed

**Sources:**
- Central Pollution Control Board (CPCB) India — official AQI data
- OpenWeatherMap API — global AQI estimates
- Breezometer API — hyper-local air quality
- IQAir API — community-sourced AQI

**Update Frequency:** Every 10-15 minutes

**Data Structure:**
```json
{
  "location": {"lat": 28.6139, "lon": 77.2090},
  "aqi": 350,
  "category": "Very Poor",
  "pollutants": {
    "PM2.5": 250,
    "PM10": 400,
    "NO2": 120,
    "SO2": 45,
    "CO": 2.5,
    "O3": 15
  },
  "timestamp": "2026-03-01T14:30:00Z"
}
```

**Spatial Interpolation:** For areas without direct monitoring, use inverse distance weighting (IDW) to estimate AQI from nearby stations.

---

#### 4.2 Satellite Imagery & Greenery Data

**Sources:**
- Sentinel-2 (ESA, free, 10m resolution, 5-day revisit)
- Planet Labs (commercial, 3m resolution, daily)
- USGS Landsat (free, 30m resolution, 16-day revisit)

**Processing:**
- NDVI (Normalized Difference Vegetation Index) calculation for each pixel
- Threshold NDVI > 0.4 to classify as "vegetation"
- Aggregate to road segment level (average canopy %)
- Cache results, update monthly

---

#### 4.3 Traffic Data

**Sources:**
- Google Maps Traffic API
- TomTom Traffic API
- Local city traffic agencies (Delhi Traffic Police, Mumbai Police, etc.)
- Connected vehicles (crowdsourced from user GPS traces)

**Update Frequency:** Real-time (1-5 minute intervals)

**Data Structure:**
```json
{
  "road_segment_id": "osm_way_12345",
  "current_speed": 15,
  "free_flow_speed": 50,
  "congestion_level": 0.7,
  "timestamp": "2026-03-01T14:35:22Z"
}
```

---

#### 4.4 Elevation & DEM Data

**Sources:**
- SRTM 30m DEM (USGS)
- GEBCO (global bathymetry)
- Google Elevation API

**Update Frequency:** Static (updated annually at most)

**Caching Strategy:** Pre-compute all gradients during system initialization; cache indefinitely.

---

#### 4.5 Public Transit APIs

**Sources:**
- Delhi Metro Rail Corporation (DMRC) API
- Mumbai Metro Rail Corporation (MMRC) API
- Bangalore Metro Rail Corporation (BMRC) API
- Local bus agencies (MTC, BMTC, ST, etc.)

**Data Required:**
- Station locations & schedules
- Real-time train/bus positions
- Line maps and transfer points

---

### 5. Database Layer

#### 5.1 Primary Database (PostgreSQL + PostGIS)

**Purpose:** Persistent storage of user data, trip history, routes, carpool matches

**Schema Overview:**

```sql
-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE,
    email VARCHAR(255),
    vehicle_type ENUM('ice', 'ev', 'hybrid'),
    carpool_rating FLOAT DEFAULT 4.5,
    eco_score_lifetime INT DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Trip History Table
CREATE TABLE trips (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    origin GEOGRAPHY(POINT),
    destination GEOGRAPHY(POINT),
    departure_time TIMESTAMP,
    arrival_time TIMESTAMP,
    distance_km FLOAT,
    route_type ENUM('driving', 'carpool', 'multimodal'),
    eco_cost_score FLOAT,
    actual_co2_kg FLOAT,
    carbon_saved_kg FLOAT,
    aqi_at_destination INT,
    carpool_matched BOOLEAN,
    num_passengers INT,
    feedback_rating INT,
    created_at TIMESTAMP
);

-- Routes Cache Table (for frequently requested routes)
CREATE TABLE route_cache (
    id UUID PRIMARY KEY,
    origin GEOGRAPHY(POINT),
    destination GEOGRAPHY(POINT),
    route_json JSONB,
    eco_cost FLOAT,
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    hit_count INT DEFAULT 0
);

-- Road Segments Table (with precomputed values)
CREATE TABLE road_segments (
    id UUID PRIMARY KEY,
    osm_way_id BIGINT,
    geom GEOMETRY(LINESTRING),
    length_km FLOAT,
    gradient_percent FLOAT,
    canopy_density FLOAT,
    canyon_index FLOAT,
    is_trap_zone BOOLEAN,
    speed_limit INT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Real-time AQI Cache
CREATE TABLE aqi_readings (
    id UUID PRIMARY KEY,
    location GEOGRAPHY(POINT),
    aqi_value INT,
    category VARCHAR(50),
    pollutants JSONB,
    source VARCHAR(50),
    timestamp TIMESTAMP,
    expires_at TIMESTAMP
);

-- Carpool Matches Table
CREATE TABLE carpool_matches (
    id UUID PRIMARY KEY,
    driver_id UUID REFERENCES users(id),
    rider_id UUID REFERENCES users(id),
    route_id UUID REFERENCES route_cache(id),
    match_score FLOAT,
    match_time TIMESTAMP,
    status ENUM('matched', 'accepted', 'completed', 'cancelled'),
    shared_distance_km FLOAT,
    cost_split JSONB,
    driver_rating_given INT,
    rider_rating_given INT,
    created_at TIMESTAMP
);

-- User Preferences Table
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY,
    user_id UUID UNIQUE REFERENCES users(id),
    prefer_carpool BOOLEAN DEFAULT TRUE,
    prefer_multimodal BOOLEAN DEFAULT TRUE,
    avoid_gradients_above FLOAT DEFAULT 8.0,
    avoid_aqi_above INT DEFAULT 400,
    prefer_greenery BOOLEAN DEFAULT TRUE,
    max_detour_minutes INT DEFAULT 10,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Create spatial indices
CREATE INDEX idx_road_segments_geom ON road_segments USING GIST (geom);
CREATE INDEX idx_trips_origin ON trips USING GIST (origin);
CREATE INDEX idx_trips_destination ON trips USING GIST (destination);
CREATE INDEX idx_aqi_readings_location ON aqi_readings USING GIST (location);
```

---

#### 5.2 Cache Layer (Redis)

**Purpose:** Fast access to frequently requested data

**Cache Keys:**

| Key | TTL | Purpose |
|-----|-----|---------|
| `route:{origin}:{destination}:{time}` | 30 min | Cached eco-optimal routes |
| `aqi:{lat}:{lon}` | 15 min | Cached AQI readings |
| `traffic:{way_id}` | 2 min | Current congestion |
| `carpool:active:{location}:{time}` | 5 min | Active carpool requests |
| `user:{user_id}:profile` | 1 hour | User preferences |
| `weights:dynamic:{time_of_day}` | 30 min | Dynamic weight presets |

---

## API Specification

### 1. Route Calculation Endpoint

**Endpoint:** `POST /api/v1/routes/calculate`

**Request:**
```json
{
  "origin": {
    "latitude": 28.6139,
    "longitude": 77.2090,
    "address": "Connaught Place, Delhi"
  },
  "destination": {
    "latitude": 28.5244,
    "longitude": 77.1855,
    "address": "India Gate, Delhi"
  },
  "departure_time": "2026-03-01T14:30:00Z",
  "vehicle_type": "ice",
  "constraints": {
    "max_gradient_percent": 8.0,
    "avoid_aqi_above": 400,
    "max_detour_minutes": 10
  },
  "preferences": {
    "allow_carpool": true,
    "allow_multimodal": true,
    "prioritize_greenery": true
  }
}
```

**Response:**
```json
{
  "status": "success",
  "routes": [
    {
      "route_id": "route_abc123",
      "rank": 1,
      "eco_cost_score": 245.3,
      "summary": {
        "total_distance_km": 12.5,
        "estimated_time_minutes": 28,
        "estimated_co2_kg": 2.8,
        "carbon_offset_kg": 0.4,
        "route_type": "driving",
        "greenery_exposure": 65
      },
      "detailed_segments": [
        {
          "segment_id": "seg_001",
          "start": {"lat": 28.6139, "lon": 77.2090},
          "end": {"lat": 28.6100, "lon": 77.2050},
          "distance_km": 0.5,
          "estimated_time_seconds": 45,
          "eco_cost_components": {
            "traffic_penalty": 15.2,
            "aqi_penalty": 10.5,
            "gradient_penalty": 5.0,
            "carpool_bonus": 0,
            "greenery_bonus": -5.2
          },
          "current_conditions": {
            "aqi": 320,
            "traffic_congestion": 0.4,
            "wind_speed_kmh": 8.5
          }
        }
      ],
      "carpool_opportunity": {
        "available": true,
        "matched_riders": 2,
        "potential_savings_minutes": 8,
        "eco_cost_if_carpooled": 180.5,
        "carpool_rider_ids": ["rider_123", "rider_456"]
      },
      "multimodal_option": {
        "available": false,
        "reason": "Destination AQI is acceptable (320 < 400)"
      },
      "polyline": "encoded_polyline_string...",
      "geojson": {
        "type": "Feature",
        "geometry": {
          "type": "LineString",
          "coordinates": [[77.2090, 28.6139], [...]]
        }
      }
    },
    {
      "route_id": "route_def456",
      "rank": 2,
      "eco_cost_score": 258.7,
      "summary": {
        "total_distance_km": 11.8,
        "estimated_time_minutes": 35,
        "estimated_co2_kg": 2.5,
        "carbon_offset_kg": 0.6,
        "route_type": "driving",
        "greenery_exposure": 78
      }
      // ... (more details)
    },
    {
      "route_id": "route_ghi789",
      "rank": 3,
      "eco_cost_score": 275.2,
      "summary": {
        "total_distance_km": 13.2,
        "estimated_time_minutes": 22,
        "estimated_co2_kg": 3.1,
        "carbon_offset_kg": 0.2,
        "route_type": "multimodal",
        "greenery_exposure": 55
      },
      "multimodal_breakdown": {
        "driving_portion": {
          "distance_km": 8.5,
          "destination": "Rajiv Chowk Metro Station"
        },
        "transit_portion": {
          "mode": "metro",
          "line": "Blue Line",
          "stations": ["Rajiv Chowk", "Charing Cross", "South Extension"],
          "estimated_time_minutes": 8,
          "transfer_time_minutes": 3
        },
        "walking_portion": {
          "distance_km": 0.3,
          "estimated_time_minutes": 5
        }
      }
    }
  ],
  "metadata": {
    "calculation_time_ms": 340,
    "data_freshness": {
      "aqi_data_age_minutes": 5,
      "traffic_data_age_minutes": 2,
      "satellite_data_age_days": 8
    },
    "region_warnings": [
      {
        "type": "aqi_alert",
        "severity": "high",
        "message": "Very Poor air quality detected. Consider multimodal or carpool options.",
        "affected_areas": ["Central Delhi"]
      }
    ]
  }
}
```

**Error Response:**
```json
{
  "status": "error",
  "error_code": "NO_ROUTE_FOUND",
  "message": "No valid route found meeting constraints",
  "suggestions": [
    "Relax gradient constraint",
    "Increase AQI threshold",
    "Increase maximum detour time"
  ]
}
```

---

### 2. Carpool Match Endpoint

**Endpoint:** `POST /api/v1/carpool/match`

**Request:**
```json
{
  "route_id": "route_abc123",
  "driver_id": "user_123",
  "available_seats": 3,
  "willing_detour_minutes": 5
}
```

**Response:**
```json
{
  "status": "success",
  "matches": [
    {
      "match_id": "match_001",
      "rider_id": "user_456",
      "rider_name": "Priya",
      "rider_rating": 4.8,
      "match_score": 0.92,
      "shared_distance_km": 10.2,
      "pickup_location": {"lat": 28.6120, "lon": 77.2085},
      "dropoff_location": {"lat": 28.5250, "lon": 77.1860},
      "time_delta_minutes": 2,
      "estimated_cost_split": {
        "driver_receives": 45,
        "rider_pays": 45,
        "currency": "INR"
      }
    },
    {
      "match_id": "match_002",
      "rider_id": "user_789",
      "rider_name": "Aman",
      "rider_rating": 4.6,
      "match_score": 0.78,
      // ... (more details)
    }
  ],
  "eco_impact": {
    "vehicles_removed_from_route": 2,
    "estimated_co2_saved_kg": 1.2,
    "traffic_reduction_percent": 8.5
  }
}
```

---

### 3. AQI Status Endpoint

**Endpoint:** `GET /api/v1/aqi/status?lat={lat}&lon={lon}&radius_km={radius}`

**Response:**
```json
{
  "status": "success",
  "center_location": {"lat": 28.6139, "lon": 77.2090},
  "aqi_readings": [
    {
      "location": "Connaught Place",
      "aqi": 350,
      "category": "Very Poor",
      "pollutants": {
        "PM2.5": 250,
        "PM10": 400,
        "NO2": 120
      },
      "source": "CPCB"
    }
  ],
  "grid": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [77.2090, 28.6139]},
        "properties": {"aqi": 350, "category": "Very Poor"}
      }
    ]
  }
}
```

---

### 4. Trip Feedback Endpoint

**Endpoint:** `POST /api/v1/feedback/trip`

**Request:**
```json
{
  "trip_id": "trip_xyz123",
  "route_id": "route_abc123",
  "user_id": "user_123",
  "actual_arrival_time": "2026-03-01T14:58:00Z",
  "actual_co2_kg": 2.7,
  "route_rating": 4,
  "comments": "Good route, avoided traffic!",
  "carpool_rating": 5,
  "carpool_driver_id": "user_456"
}
```

**Response:**
```json
{
  "status": "success",
  "feedback_recorded": true,
  "eco_points_earned": 45,
  "user_eco_score_updated": 2845
}
```

---

## Algorithm & Heuristic Design

### Eco-Cost Heuristic Deep Dive

#### Weight Adjustment Algorithm

The core of EcoPath's intelligence lies in dynamic weight adjustment. Rather than static weights, the system adapts based on real-time conditions:

**Variables Affecting Weights:**

1. **Time of Day**
   - Peak hours (7-9 AM, 5-7 PM): Increase W₁ (traffic) by 1.5x
   - Off-peak hours: Decrease W₁ by 0.8x

2. **Weather Conditions**
   - Clear weather: Base weights
   - Monsoon: Increase W₃ (gradient) by 1.2x (wet roads = lower traction)
   - Heat wave (temp > 40°C): Increase W₅ (greenery) by 1.3x (cooling critical)
   - Dust storm: Increase W₂ (AQI) by 2.0x

3. **AQI Emergency Level**
   - Green (0-50): Base AQI weight
   - Yellow (51-100): W₂ × 1.2
   - Orange (101-200): W₂ × 1.5
   - Red (201-400): W₂ × 2.0
   - Maroon/Purple (>400): W₂ × 3.0 + activate multimodal suggestions

4. **Day Type**
   - Weekday: Standard weights
   - Weekend: Decrease W₁ (traffic less critical)
   - Holiday: Different traffic patterns

5. **Vehicle Type**
   - EV: Reduce W₃ (gradient irrelevant, battery recovery on downhill)
   - ICE: Standard weights
   - Hybrid: Reduce W₃ by 0.5x (partial electric assist)

**Weight Normalization:**
```python
def normalize_weights(W1, W2, W3, W4, W5):
    total = W1 + W2 + W3 + W4 + W5
    return {
        'W1': W1 / total,
        'W2': W2 / total,
        'W3': W3 / total,
        'W4': W4 / total,
        'W5': W5 / total
    }
```

---

#### Eco-Cost Component Calculations

**1. Traffic Component**

```python
def calculate_traffic_penalty(current_speed, free_flow_speed):
    # Congestion ratio: 0 = free-flow, 1 = stopped
    congestion_ratio = 1 - (current_speed / free_flow_speed)
    
    # Convert to 0-100 penalty scale
    penalty = congestion_ratio * 100
    
    # Amplify minor congestion (drivers accelerate/brake frequently)
    if congestion_ratio > 0.7:
        penalty *= 1.3  # Heavy congestion = amplified emissions
    
    return min(penalty, 100)
```

**2. AQI Component**

```python
def calculate_aqi_penalty(aqi_value):
    # Normalize AQI to 0-100 scale
    # Base: AQI 300 = penalty 50
    if aqi_value <= 50:
        penalty = 5
    elif aqi_value <= 100:
        penalty = 10
    elif aqi_value <= 200:
        penalty = 30
    elif aqi_value <= 300:
        penalty = 50
    elif aqi_value <= 400:
        penalty = 75
    else:
        penalty = 100  # Hazardous level
    
    return penalty
```

**3. Gradient Component**

```python
def calculate_gradient_penalty(gradient_percent):
    # Base: 0% gradient = 0 penalty
    # 5% gradient = 40 penalty (reference point)
    # 10% gradient = 100 penalty (severe)
    
    if gradient_percent <= 1:
        penalty = 0
    elif gradient_percent <= 3:
        penalty = gradient_percent * 5
    elif gradient_percent <= 6:
        penalty = 15 + (gradient_percent - 3) * 8
    else:
        penalty = min(39 + (gradient_percent - 6) * 10, 100)
    
    return penalty
```

**4. Carpool Bonus**

```python
def calculate_carpool_bonus(num_matched_riders):
    # Bonus increases with number of riders
    # 1 rider: -5 (small bonus)
    # 2 riders: -12 (medium bonus)
    # 3+ riders: -20 (large bonus, vehicle reduction)
    
    if num_matched_riders == 0:
        return 0
    elif num_matched_riders == 1:
        return -5
    elif num_matched_riders == 2:
        return -12
    else:
        return -20
```

**5. Greenery Bonus**

```python
def calculate_greenery_bonus(canopy_density_percent):
    # Bonus based on tree coverage
    # 0% coverage: 0 bonus
    # 50% coverage: -10 bonus
    # 80%+ coverage: -20 bonus
    
    if canopy_density_percent < 30:
        return 0
    elif canopy_density_percent < 50:
        return -(canopy_density_percent - 30) * 0.5
    elif canopy_density_percent < 70:
        return -10 - (canopy_density_percent - 50) * 0.5
    else:
        return -20  # Maximum greenery bonus
```

---

### Pathfinding Algorithm

**Modified Dijkstra with A* Heuristic:**

```python
def dijkstra_eco_optimal(graph, start, goal, weights, constraints):
    import heapq
    
    # Priority queue: (eco_cost, node, path)
    open_set = [(0, start, [start])]
    closed_set = set()
    cost_to = {start: 0}
    
    while open_set:
        current_cost, current_node, path = heapq.heappop(open_set)
        
        if current_node in closed_set:
            continue
        
        if current_node == goal:
            return path  # Found optimal route
        
        closed_set.add(current_node)
        
        # Explore neighbors
        for neighbor_node, edge in graph.neighbors(current_node):
            # Check constraints
            if violates_constraints(edge, constraints):
                continue
            
            # Calculate eco-cost of edge
            eco_cost = calculate_eco_cost(edge, weights)
            new_cost = cost_to[current_node] + eco_cost
            
            if neighbor_node not in cost_to or new_cost < cost_to[neighbor_node]:
                cost_to[neighbor_node] = new_cost
                
                # A* heuristic: euclidean distance to goal
                heuristic = euclidean_distance(neighbor_node, goal)
                priority = new_cost + heuristic
                
                heapq.heappush(open_set, (priority, neighbor_node, path + [neighbor_node]))
    
    return None  # No route found
```

---

## Technology Stack

### Backend

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **API Framework** | FastAPI (Python) | Async, fast, built-in OpenAPI docs |
| **Pathfinding** | NetworkX (Python) | Graph algorithms, Dijkstra support |
| **Geospatial** | PostGIS (PostgreSQL) | Spatial queries, distance calculations |
| **Caching** | Redis | Sub-millisecond latency for hot data |
| **ML/CV** | TensorFlow/PyTorch + OpenCV | CNN for greenery detection |
| **Data Processing** | Pandas + NumPy | Data wrangling, calculations |
| **Web Server** | Uvicorn | ASGI server for FastAPI |
| **Container** | Docker | Reproducible deployment |
| **Orchestration** | Kubernetes (optional) | Horizontal scaling |

### Frontend

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Mobile** | React Native or Flutter | Cross-platform (iOS + Android) |
| **Web** | React.js + TypeScript | Type-safe, component reusability |
| **Mapping** | Mapbox GL or Leaflet | Real-time route visualization |
| **UI** | Material-UI or Tailwind CSS | Professional, accessible design |
| **State Management** | Redux or Zustand | Predictable state management |

### Data Pipeline

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Satellite Imagery** | Sentinel-2 API or Planet Labs | Greenery detection |
| **DEM/Elevation** | SRTM or Google Elevation API | Gradient calculations |
| **AQI Data** | CPCB API + OpenWeatherMap | Real-time pollution data |
| **Traffic** | Google Maps API or TomTom | Real-time congestion |
| **OSM Data** | OpenStreetMap Overpass API | Road network, building data |
| **Batch Processing** | Apache Airflow | Scheduled data updates |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Cloud Provider** | AWS / GCP / Azure | Hosting, scalability |
| **Database** | PostgreSQL + PostGIS | Relational + geospatial |
| **Cache** | Redis | Sub-millisecond lookups |
| **Message Queue** | RabbitMQ or Kafka | Async job processing |
| **Monitoring** | Prometheus + Grafana | System health, alerting |
| **Logging** | ELK Stack (Elasticsearch, Logstash, Kibana) | Centralized logging |

---

## Data Flow Diagrams

### User Route Request Flow

```
┌──────────────┐
│  User Opens  │
│ EcoPath App  │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ Input: Origin +      │
│ Destination +        │
│ Preferences          │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────────┐
│   API Gateway                    │
│   (Validate, Auth, Rate Limit)   │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  Check Route Cache (Redis)       │
│  ├─ HIT: Return cached route     │
│  └─ MISS: Proceed to calculation │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  Fetch Real-time Data            │
│  ├─ Current AQI (CPCB API)       │
│  ├─ Traffic (Google Maps API)    │
│  ├─ Weather (OpenWeatherMap)     │
│  └─ Wind patterns (Local API)    │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  Build Road Graph                │
│  ├─ Load OSM road network        │
│  ├─ Add elevation data (SRTM)    │
│  ├─ Add precomputed attributes   │
│  │  ├─ Gradient per segment      │
│  │  ├─ Greenery density          │
│  │  └─ Canyon index              │
│  └─ Add real-time attributes     │
│     ├─ Traffic speed             │
│     └─ AQI at location           │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  Calculate Dynamic Weights       │
│  ├─ Time of day                  │
│  ├─ Weather conditions           │
│  ├─ AQI alert level              │
│  └─ Vehicle type                 │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  Run Dijkstra + A* Pathfinding   │
│  ├─ Compute eco-cost for each    │
│  │  road segment in graph        │
│  ├─ Find global minimum path     │
│  └─ Generate K-best alternatives │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  Evaluate Carpool Opportunities  │
│  ├─ Query active riders in Redis │
│  ├─ Match by route overlap       │
│  └─ Score matches by compatibility
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  Evaluate Multi-modal Options    │
│  ├─ Check destination AQI        │
│  ├─ If hazardous:                │
│  │  ├─ Suggest Park & Walk       │
│  │  └─ Suggest Park & Ride       │
│  └─ Calculate multi-modal routes │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  Format Response                 │
│  ├─ Route 1 (best eco-cost)      │
│  ├─ Route 2 (alternative)        │
│  ├─ Route 3 (multi-modal)        │
│  └─ Metadata (freshness, alerts) │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  Cache Route (Redis TTL=30min)   │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  Return JSON Response to Client  │
└──────────────────────────────────┘
```

### Carpool Matching Flow

```
┌──────────────────────────┐
│ Driver Accepts Route     │
│ & Initiates Carpool      │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ Check if Route is        │
│ "Red Zone"               │
│ (congestion + AQI high)  │
└──────────┬───────────────┘
           │
       YES│
           ▼
┌──────────────────────────────────────┐
│ Query Redis for Active Riders        │
│ ├─ Origin within 500m radius         │
│ ├─ Destination within 500m radius    │
│ ├─ Departure time ±10 minutes        │
│ └─ Status = waiting                  │
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ Calculate Route Overlap for Each     │
│ Potential Rider                      │
│ ├─ Spatial matching (Frechet dist)   │
│ ├─ Time matching (departure delta)   │
│ ├─ User rating filtering (>4.0)      │
│ └─ Score matches 0-1.0               │
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ Return Top 3 Matches to Driver       │
│ ├─ Driver can accept/decline         │
│ └─ Carpool eco-cost recalculated     │
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ Accepted: Send Offer to Rider        │
│ (Real-time notification)             │
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ If Rider Accepts:                    │
│ ├─ Create carpool_matches record     │
│ ├─ Update driver & rider status      │
│ ├─ Lock eco-score reduction          │
│ ├─ Push cost-split details           │
│ └─ Notify both parties               │
└──────────────────────────────────────┘
```

---

## Deployment Strategy

### Development Environment

```
Local Machine (Dev)
├─ Python 3.9+
├─ PostgreSQL (local Docker container)
├─ Redis (local Docker container)
└─ FastAPI server (uvicorn)
```

### Staging Environment

```
AWS/GCP/Azure (Staging)
├─ RDS PostgreSQL (multi-zone)
├─ ElastiCache Redis
├─ ECS/Cloud Run (containerized FastAPI)
├─ S3/Cloud Storage (cache, imagery)
└─ CloudFront/CDN (API distribution)
```

### Production Environment

```
AWS/GCP/Azure (Production)
├─ Multi-region database (PostgreSQL RDS)
├─ Multi-region Redis (read replicas)
├─ Kubernetes cluster (auto-scaling)
│  ├─ API service pods (min 5, max 20)
│  ├─ Carpool matching service
│  ├─ Weight adjuster service
│  └─ Data integration service
├─ Message Queue (RabbitMQ / Kafka)
├─ S3/Cloud Storage (multi-region)
├─ CloudFront/CDN
├─ Load Balancer (multi-region)
├─ Monitoring (Prometheus + Grafana)
└─ Logging (ELK Stack)
```

### CI/CD Pipeline

```
GitHub (Code Repo)
   │
   ▼
GitHub Actions / GitLab CI
   │
   ├─ Run Tests (unit + integration)
   ├─ Lint Code (flake8, black)
   ├─ Build Docker Image
   ├─ Push to Container Registry (ECR/GCR)
   │
   ├─ Deploy to Staging
   │  ├─ Run smoke tests
   │  ├─ Load test
   │  └─ Manual approval
   │
   └─ Deploy to Production
      ├─ Blue-Green deployment
      ├─ Canary rollout (10% → 50% → 100%)
      └─ Monitoring + auto-rollback
```

---

## Scalability & Performance Considerations

### Route Calculation Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| **Route calc time** | < 500ms | P95 latency |
| **Cache hit rate** | > 70% | For frequent routes |
| **Carpool match time** | < 200ms | Real-time matching |
| **API response time** | < 800ms | Full stack |
| **Throughput** | 1000 req/sec | Peak capacity |

### Optimization Strategies

**1. Route Caching**
- Cache routes by (origin, destination, time_window)
- TTL: 30 minutes (traffic changes frequently)
- Hit rate: ~70% (many users have common routes)

**2. Graph Pre-computation**
- Pre-compute gradients for all road segments (static, done once)
- Pre-compute greenery density from satellite data (monthly refresh)
- Pre-compute canyon index for major corridors (quarterly refresh)
- Store in database with fast spatial indices

**3. Real-time Data Partitioning**
- Partition AQI data by geographic regions (grid cells)
- Cache AQI per cell (TTL: 15 minutes)
- Use spatial interpolation for coverage gaps

**4. K-best Path Optimization**
- Instead of full re-compute, return cached top-3 routes
- Only re-rank if real-time data significantly changes
- Use branch-and-bound to prune search space

**5. Carpool Matching Optimization**
- Maintain spatial index of active riders (Redis)
- Use radius search (not full DB query)
- Limit to top 100 candidates, then score

**6. Load Balancing**
- API Gateway distributes requests across server pool
- Sticky sessions for user state
- Geographic distribution (edge servers in India)

### Database Optimization

**Indices:**
```sql
-- Spatial indices for fast geographic queries
CREATE INDEX idx_road_segments_geom ON road_segments USING GIST (geom);
CREATE INDEX idx_aqi_readings_location ON aqi_readings USING GIST (location);

-- Temporal indices for time-based queries
CREATE INDEX idx_trips_created_at ON trips (created_at DESC);

-- Partial indices for common filters
CREATE INDEX idx_carpool_matches_active 
  ON carpool_matches (created_at DESC) 
  WHERE status IN ('matched', 'accepted');

-- Foreign key indices
CREATE INDEX idx_trips_user_id ON trips (user_id);
CREATE INDEX idx_carpool_matches_driver ON carpool_matches (driver_id);
```

**Connection Pooling:**
- PgBouncer for PostgreSQL connection management
- Min pool: 5, Max pool: 50 per server
- Redis connection pool: 10-20 connections

**Query Optimization:**
- Avoid N+1 queries (use JOINs)
- Use prepared statements (prevent SQL injection + faster parsing)
- Batch inserts for trip history
- EXPLAIN ANALYZE for query plans

---

## Summary

This architecture provides:

✅ **Scalability:** Horizontal scaling via Kubernetes, caching layers, and data partitioning  
✅ **Real-time Performance:** Sub-second route calculations with caching and pre-computation  
✅ **Reliability:** Multi-region failover, monitoring, and auto-recovery  
✅ **Data Integrity:** PostgreSQL with ACID guarantees, backup strategy  
✅ **User Experience:** Comprehensive routing options (driving, carpool, multimodal)  
✅ **Environmental Impact:** Multi-factor optimization (emissions, air quality, greenery)

---

**Next Steps:**
1. Implement core pathfinding engine (Dijkstra + weights)
2. Build API routes and data models
3. Integrate real-time data sources (AQI, traffic)
4. Develop ML models (greenery detection, canyon classification)
5. Build frontend interfaces (mobile + web)
6. Deploy to staging environment
7. Conduct performance testing and optimization
8. Launch pilot in one Indian metro (Delhi or Bangalore)
