# KidneyStoneAI Platform

> **AI-Powered Reliable Clinical Decision Support Platform for Kidney Stone Diagnosis Using Explainable AI and Intelligent Microservice Dependency Analysis**

---

## Project Overview

KidneyStoneAI is a production-grade, cloud-ready healthcare platform built on a **Microservices Architecture** using **Spring Boot (Java 21)**, a **Python AI Engine (PyTorch + Ultralytics YOLO11 + U-Net)**, and a **React TypeScript** frontend — all orchestrated through **Docker Compose**.

The system provides:

| Capability | Technology |
|---|---|
| Kidney Stone Detection | Ultralytics YOLO11 |
| Stone Segmentation | U-Net |
| Severity Assessment | Ensemble Severity Prediction (Random Forest + Clinical Features + Image Features) |
| Treatment Recommendation | Evidence-Based Rules Engine |
| Explainable AI | GradCAM Heatmaps |
| Microservice Health Monitoring | Spring Boot Actuator + Prometheus |
| Cascading Failure Prediction | NetworkX + Random Forest |
| Root Cause Analysis | Dependency Graph Analysis |

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS |
| **API Gateway** | Spring Cloud Gateway |
| **Backend Services** | Java 21, Spring Boot 3.2, Spring Security, JWT |
| **AI Engine** | Python 3.11, FastAPI, PyTorch, Ultralytics YOLO11, U-Net, GradCAM |
| **Database** | PostgreSQL 15 (multiple schemas) |
| **Monitoring** | Prometheus + Grafana |
| **Containerization** | Docker + Docker Compose |

---

## Architecture

```
Doctor / Admin
       │
React Frontend  (port 3000)
       │
API Gateway     (port 8080)  ← ONLY public entry point
       │
┌──────────────────────────────────────────────────────┐
│ Authentication Service  (8081)                        │
│ Patient Service         (8082)                        │
│ Image Service           (8083)                        │
│ Diagnosis Service       (8084) ──► Python AI Engine  │
│ Severity Service        (8085) ──► (port 5000)       │
│ Treatment Service       (8086)                        │
│ Report Service          (8087)                        │
│ Monitoring Service      (8088)                        │
│ Dependency Analyzer     (8089)                        │
└──────────────────────────────────────────────────────┘
       │
PostgreSQL (port 5432)
```

---

## Project Structure

```
KidneyStoneAI/
├── backend/
│   ├── api-gateway/
│   ├── authentication-service/
│   ├── patient-service/
│   ├── image-service/
│   ├── diagnosis-service/
│   ├── severity-service/
│   ├── treatment-service/
│   ├── report-service/
│   ├── monitoring-service/
│   └── dependency-analyzer-service/
├── frontend/
├── ai-engine/
├── database/
│   └── schema/
├── docker/
│   └── prometheus/
├── monitoring/
├── testing/
├── docs/
├── datasets/
├── deployment/
├── diagrams/
├── rulebook/      ← project constitution & standards
├── docker-compose.yml
├── pom.xml         ← Maven parent POM
└── README.md
```

---

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose v2
- Java 21 (for local backend development)
- Node 20+ (for local frontend development)
- Python 3.11+ (for AI engine development)

### 1. Configure Environment

```bash
cp .env.example .env
# Edit .env and set all required secrets
```

### 2. Run with Docker Compose

```bash
docker compose up --build
```

### 3. Access Services

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API Gateway | http://localhost:8080 |
| Swagger UI (Auth) | http://localhost:8081/swagger-ui.html |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |

---

## Development Setup

### Backend (Spring Boot)

```bash
# Build all services from parent POM
mvn clean install -DskipTests

# Run a specific service
cd backend/authentication-service
mvn spring-boot:run -Dspring-boot.run.profiles=dev
```

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

### AI Engine (Python)

```bash
cd ai-engine
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn api.main:app --reload --port 5000
```

---

## Documentation

| Document | Location |
|---|---|
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Database Design | [docs/DATABASE.md](docs/DATABASE.md) |
| API Specification | [docs/API_SPEC.md](docs/API_SPEC.md) |
| Security Guide | [docs/SECURITY.md](docs/SECURITY.md) |
| AI Rulebook | [rulebook/AI_RULEBOOK.md](rulebook/AI_RULEBOOK.md) |
| Coding Standards | [rulebook/CODING_STANDARD.md](rulebook/CODING_STANDARD.md) |
| Project Manifest | [rulebook/PROJECT_MANIFEST.md](rulebook/PROJECT_MANIFEST.md) |

---

## Security Notes

- All secrets are environment-variable-driven. Never commit `.env`.
- JWT tokens must be signed with a minimum 64-character secret.
- Patient records implement **soft delete** — never deleted permanently.
- All API calls require JWT except `/login`, `/register`, `/forgot-password`.

---

## Contributing

Follow the [AI_RULEBOOK.md](rulebook/AI_RULEBOOK.md) and [CODING_STANDARD.md](rulebook/CODING_STANDARD.md) strictly.

Branch strategy:
- `main` — always stable
- `develop` — current work
- `feature/<name>` — every feature

---

## Status

> **Sprint 0 — Project Scaffolding Complete. Architecture and folder structure initialized. No business logic implemented yet.**
