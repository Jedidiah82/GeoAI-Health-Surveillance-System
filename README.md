# GeoAI Health Surveillance System

Privacy-preserving operational GeoAI surveillance platform integrating geospatial intelligence, explainable artificial intelligence (XAI), secure API mediation, and governance-aware hybrid cloud architecture for district-level outbreak risk monitoring.

---

# Overview

This project presents an operational GeoAI surveillance prototype designed to support district-level epidemiological monitoring and spatial intelligence using:

- GeoAI prediction models
- Spatial hotspot analysis
- Explainable AI (SHAP)
- Interactive GIS dashboards
- Secure FastAPI gateway
- JWT authentication
- Role-based access control (RBAC)
- Audit logging
- Dockerized deployment workflow

The system was developed as part of an MSc Big Data Technologies dissertation focused on:

> Design and Evaluation of a Privacy-Preserving GeoAI Health Surveillance System Using a Hybrid Cloud Architecture

---

# Core Features

## Operational GeoAI Dashboard
- Interactive Streamlit dashboard
- District-level outbreak monitoring
- KPI intelligence cards
- Temporal outbreak trends
- Environmental and epidemiological indicators

## Spatial Intelligence
- Interactive Folium GIS map
- GeoAI outbreak probability mapping
- Risk classification visualization
- Getis-Ord Gi* hotspot analysis
- Local Moran’s I (LISA) cluster analysis

## Explainable GeoAI
- SHAP explainability outputs
- Feature importance analysis
- XGBoost model interpretation
- Model confidence evaluation

## Governance & Security
- JWT authentication
- RBAC-style access control
- Secure FastAPI API gateway
- Operational audit logging
- Governance traceability

## Deployment & Packaging
- Dockerized architecture
- docker-compose integration
- GitHub version control
- Cloud deployment ready

---

# System Architecture

The platform implements a governance-aware hybrid GeoAI architecture consisting of:

1. Secure Data Governance Layer
2. Secure API Mediation Layer
3. GeoAI Analytics Layer
4. Explainability & Decision Support Layer
5. Operational Dashboard Interface

---

# Technology Stack

## GIS & Spatial Analytics
- ArcGIS Pro
- GeoPandas
- Folium
- Shapely
- PySAL

## Machine Learning & Explainability
- Scikit-learn
- XGBoost
- SHAP
- Pandas
- NumPy

## Dashboard & API
- Streamlit
- FastAPI
- Uvicorn

## Security & Governance
- JWT Authentication
- OAuth2PasswordBearer
- RBAC-style authorization
- Audit logging

## Deployment
- Docker
- docker-compose
- GitHub

---

# Repository Structure

```text
GeoAI_Surveillance_System/
│
├── app/
│   ├── api.py
│   ├── auth.py
│   ├── dashboard.py
│   ├── map_utils.py
│   ├── audit_logger.py
│   ├── refresh_simulator.py
│   └── model_engine.py
│
├── data/
│
├── figures/
│   ├── maps/
│   └── shap/
│
├── logs/
│
├── models/
│
├── tests/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# Running the Streamlit Dashboard

## Local Execution

```bash
streamlit run app/dashboard.py
```

Dashboard URL:

```text
http://localhost:8501
```

---

# Running the FastAPI Secure Gateway

## Local Execution

```bash
uvicorn app.api:app --reload
```

API URL:

```text
http://127.0.0.1:8000
```

Swagger/OpenAPI Documentation:

```text
http://127.0.0.1:8000/docs
```

---

# Docker Deployment

## Build Docker Image

```bash
docker build -t geoai-surveillance-system .
```

## Run Container

```bash
docker run -p 8501:8501 geoai-surveillance-system
```

---

# Docker Compose Deployment

## Run Full Operational Stack

```bash
docker-compose up --build
```

This launches:
- Streamlit operational dashboard
- FastAPI secure gateway

---

# Security Features

The platform demonstrates:

- Secure API mediation
- JWT-based authentication
- Governance-aware access control
- Operational audit logging
- Privacy-preserving analytics
- Aggregated district-level surveillance intelligence

No personally identifiable information (PII) is stored or exposed within the prototype.

---

# Explainable AI Features

The system integrates SHAP explainability to:
- identify major outbreak drivers
- support model transparency
- improve operational interpretability
- enhance governance and trustworthiness

---

# Operational Intelligence Features

The system includes:
- outbreak probability prediction
- district-level risk ranking
- hotspot intelligence
- operational alert summaries
- environmental surveillance indicators
- model validation outputs

---

# Research Context

This repository supports MSc dissertation research in:

- GeoAI
- Spatial Epidemiology
- Explainable AI (XAI)
- Hybrid Cloud Architecture
- Public Health Informatics
- Governance-aware AI Systems
- Privacy-preserving spatial analytics

---

# Author

Godwin Etim Akpan

Geospatial Data Analyst | GeoAI Researcher | Big Data Technologies MSc Candidate

GitHub:
https://github.com/Jedidiah82

---

# License

This repository is currently intended for academic research, demonstration, and educational purposes.