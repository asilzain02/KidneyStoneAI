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

> **Sprint 3 — Image Service Complete. Sprint 0 (Architecture), Sprint 1 (Authentication), Sprint 2 (Patient Management), and Sprint 3 (Image Management) are all done.**

---

## ✅ Completed Sprints

| Sprint | Scope | Status |
|---|---|---|
| Sprint 0 | Project Architecture & Scaffolding | ✅ Complete |
| Sprint 1 | Authentication Service (JWT, register, login, refresh) | ✅ Complete |
| Sprint 2 | Patient Management Service (CRUD, search, audit) | ✅ Complete |
| Sprint 3 | Image Service (upload, storage, metadata, download, delete) | ✅ Complete |

---

## Sprint 3 — Image Service

### Overview

The Image Service handles all medical image lifecycle management:

- Accepts **PNG, JPG, JPEG, DICOM (.dcm)** uploads (max **50 MB**)
- Rejects every other file type with a meaningful 400 error
- Stores binary files **on local disk** under `uploads/{patientId}/{uuid}_{originalName}`
- Persists **metadata only** in PostgreSQL (`image.medical_images` table)
- Supports future migration to MinIO / AWS S3 via the `FileStorageService` interface
- All endpoints protected with **JWT Bearer Token**

### API Endpoints

| Method | Path | Authority | Description |
|---|---|---|---|
| `POST` | `/api/v1/images/upload/{patientId}` | ROLE_ADMIN, ROLE_DOCTOR | Upload image file |
| `GET` | `/api/v1/images/{id}` | authenticated | Get image metadata by ID |
| `GET` | `/api/v1/images/patient/{patientId}` | authenticated | List all images for a patient |
| `GET` | `/api/v1/images/download/{id}` | authenticated | Download binary file |
| `DELETE` | `/api/v1/images/{id}` | ROLE_ADMIN, ROLE_DOCTOR | Soft-delete image |

### Swagger UI

```
http://localhost:8083/swagger-ui.html
```

### Supported File Types

| Extension | Content-Type | Modality |
|---|---|---|
| `.png` | image/png | IMAGE |
| `.jpg` | image/jpeg | IMAGE |
| `.jpeg` | image/jpeg | IMAGE |
| `.dcm` | application/dicom | DICOM |

### Upload Directory Structure

```
uploads/
└── {patient-uuid}/
    ├── {uuid}_scan.png
    ├── {uuid}_scan.jpg
    └── {uuid}_scan.dcm
```

The upload root defaults to `uploads/` relative to the working directory.
Override via: `UPLOAD_DIR=/path/to/uploads` environment variable.

### Image Service Folder Structure

```
image-service/src/main/java/com/kidneystone/image/
├── ImageServiceApplication.java
├── config/
│   └── ImageServiceConfig.java       ← OpenAPI + JPA Auditing
├── controller/
│   └── ImageController.java
├── dto/
│   ├── ImageUploadRequest.java
│   └── ImageResponse.java
├── entity/
│   └── MedicalImage.java
├── exception/
│   └── ImageExceptionHandler.java
├── mapper/
│   └── ImageMapper.java
├── repository/
│   └── MedicalImageRepository.java
├── security/
│   ├── JwtAuthenticationEntryPoint.java
│   ├── JwtAuthenticationFilter.java
│   ├── JwtProvider.java
│   └── SecurityConfig.java
├── service/
│   └── ImageService.java
├── storage/
│   ├── FileStorageService.java       ← interface (swappable)
│   └── LocalFileStorageService.java  ← local disk implementation
└── validation/
    └── ImageFileValidator.java
```

### Build Instructions

```bash
# From project root — builds all services including image-service
mvn clean install

# Build image-service only
cd backend/image-service
mvn clean install

# Skip tests
mvn clean install -DskipTests
```

### Manual Testing Instructions

Obtain a JWT token first:

```bash
# 1. Register / Login (auth-service on port 8081)
curl -X POST http://localhost:8081/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"doctor@example.com","password":"Password123!"}'

# Copy the accessToken from the response
TOKEN=<paste_token_here>
PATIENT_ID=<existing-patient-uuid>
```

Then run each scenario:

```bash
# Upload PNG
curl -X POST http://localhost:8083/api/v1/images/upload/$PATIENT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@scan.png"

# Upload JPG
curl -X POST http://localhost:8083/api/v1/images/upload/$PATIENT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@scan.jpg"

# Upload DICOM
curl -X POST http://localhost:8083/api/v1/images/upload/$PATIENT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@scan.dcm"

# Reject PDF (expect 400)
curl -X POST http://localhost:8083/api/v1/images/upload/$PATIENT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@report.pdf"

# Reject ZIP (expect 400)
curl -X POST http://localhost:8083/api/v1/images/upload/$PATIENT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@archive.zip"

# Download image binary
curl -X GET http://localhost:8083/api/v1/images/download/$IMAGE_ID \
  -H "Authorization: Bearer $TOKEN" --output downloaded_scan.png

# Retrieve metadata
curl -X GET http://localhost:8083/api/v1/images/$IMAGE_ID \
  -H "Authorization: Bearer $TOKEN"

# List patient images
curl -X GET http://localhost:8083/api/v1/images/patient/$PATIENT_ID \
  -H "Authorization: Bearer $TOKEN"

# Delete image
curl -X DELETE http://localhost:8083/api/v1/images/$IMAGE_ID \
  -H "Authorization: Bearer $TOKEN"
```

---

## Current Roadmap

| Sprint | Scope | Target |
|---|---|---|
| Sprint 4 | Diagnosis Service (AI integration) | Pending |
| Sprint 5 | Severity Service | Pending |
| Sprint 6 | Treatment Service | Pending |
| Sprint 7 | Report Service | Pending |
| Sprint 8 | Monitoring + Dependency Analyzer | Pending |
| Sprint 9 | Frontend (React + TypeScript) | Pending |
| Sprint 10 | AI Engine (YOLO11 + U-Net + Grad-CAM) | Pending |

---

## Known Issues / Backlog

- **JWT Swagger Testing**: Swagger UI bearer token input works but manual curl is recommended during backend-only testing. Will be validated during frontend integration.