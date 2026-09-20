# KidneyStoneAI

> **AI-Powered Clinical Decision Support Platform for Kidney Stone Diagnosis with Explainable AI and Intelligent Microservice Dependency Analysis**

---

## Project Overview

KidneyStoneAI is a production-grade healthcare platform built on a **Microservices Architecture** using **Spring Boot (Java 21)**, a **Python AI Engine (PyTorch + Ultralytics YOLO11 + U-Net)**, and a modular **React TypeScript** frontend.

The system provides:

| Capability | Technology |
|---|---|
| Kidney Stone Detection | Ultralytics YOLO11 |
| Stone Segmentation | U-Net |
| Severity Assessment | Ensemble Severity Prediction |
| Treatment Recommendation | Evidence-Based Rules Engine |
| Explainable AI | GradCAM Heatmaps |
| Microservice Health Monitoring | Spring Boot Actuator + Prometheus |
| Root Cause Analysis | Dependency Graph Analysis (Planned) |

*Note: The Intelligent Microservice Dependency Analyzer is a core planned research component of the project and is currently in development.*

---

## Technology Stack

### Frontend
- React 18, TypeScript, Vite, React Router, Tailwind CSS, Axios, React Query, Lucide-react

### Backend
- Java 21, Spring Boot 3.2, Spring Cloud Gateway, OpenFeign

### AI/ML
- Python 3.11, FastAPI, PyTorch, Ultralytics YOLO11, U-Net, GradCAM

### Database
- PostgreSQL 15

### Security
- Spring Security, JWT (JSON Web Tokens), BCrypt password hashing

### Containerization / Infrastructure
- Docker, Docker Compose

### Development
- Maven, npm

---

## Architecture

```text
                    React Frontend
                          |
                     API Gateway
                          |
       ┌──────────────────┼───────────────────┐
       ↓                  ↓                   ↓
 Authentication       Patient             Image
    Service           Service             Service
                          |
                          ↓
                   Diagnosis Service
                    /      |       \
                   ↓       ↓        ↓
              AI Engine Severity Treatment
                   |
                   ↓
                 Report
                Service
```

*Future Reliability Layer (Planned for Sprint 7)*:
```text
              Monitoring Service
                      |
                      ↓
          Dependency Analyzer
                      |
                      ↓
        Dependency / Failure Graph
```

---

## Current Implemented Features

### Authentication & Authorization
- JWT-based authentication
- Role-based authorization (Admin and Doctor clinical roles)
- Login / Logout workflows
- User management functionality (Admin-only)

*(Note: "Patient" is not a supported frontend access role. Clinical frontend scope is strictly limited to Admin and Doctor user profiles.)*

### Patient Management
- Complete CRUD workflow for patient records (managed by authenticated users)
- Patient-centric clinical flows linking directly to imagery.

### Medical Image Management
- Secure CT medical image upload, metadata extraction, and binary retrieval
- **Role Restriction:** Only users with `ROLE_ADMIN` can upload/manage CT images, while `ROLE_DOCTOR` relies upon previously staged files, ensuring strict access compliance.

### AI Diagnosis
- Efficient integration traversing data directly down to the FastAPI AI Engine.
- High-fidelity inference generating classification boundaries, segmentation overlays, and authoritative Grad-CAM AI explainability tools.
- Granular recording of inference metadata.

### Clinical Decision Support
- Aggregates predictive confidence algorithms, consistency auditing, heuristic severity assessment scoring, and targeted treatment paths.
- Provides actionable diagnostic insight generation to aid clinical decision support.

### Visualization
- The diagnostic interface displays three strictly disjoint AI visual artifacts fetched dynamically via authenticated sessions:
  1. Original CT Scanner Image
  2. AI Segmentation Visualization Overlay
  3. Grad-CAM / Classification Visualization
- *(Note: The prior artifact `GET /api/v1/diagnoses/{id}/comparison` endpoint is retained solely for legacy backend verification and Swagger testing purposes.)*

### Reporting
- Dynamic PDF-based functional clinical report flow integrating backend service layers securely.
- Connects **Selected Patient** → **Selected Diagnosis** to dynamically visualize a tailored diagnostic breakdown.
- Employs deep integration to inject actual artifact images accurately inside a generated PDF.
- Delivers instantaneous visual preview logic paired with single-click authoritative PDF blob download features.

---

## Frontend Architecture

The React frontend utilizes a modular, feature-based architecture strictly mapping closely to the backend microservices domains:

```text
frontend/src/
├── app/
├── components/
├── config/
├── features/
│   ├── auth/
│   ├── diagnoses/
│   ├── images/
│   ├── patients/
│   └── reports/
├── hooks/
├── services/
└── types/
```

### Current Workflow

**Diagnosis Page:**
1. User filters patient entities previously onboarded.
2. Selects a localized staged CT image.
3. Requests active AI analysis.
4. Immediately observes visual results on the same screen (Prediction, Confidence, Consistency, Severity, Treatment) augmented by Original CT, Segmentation, and Grad-CAM rendering profiles.

**Reports Page:**
- Clinician identifies Target Patient → Selects Diagnosis.
- Platform loads immediate UI clinical report preview visualizing textual metrics and physical clinical imagery bounds.
- System initiates secure streaming of backend dynamically rendered `KidneyStoneAI_Report_<ID>.pdf` files upon request.

**Users Page:**
- Complete interface exclusively isolated for existing Administrators bridging core roles securely.

*(Note: The Sprint 6 clinical UI is currently considered complete. The UI will be extended in Sprint 7 to integrate Monitoring and the Intelligent Microservice Dependency Analyzer. These additions will be implemented without unnecessarily restructuring the existing clinical modules.)*

---

## Microservices

The orchestrating backend platform features numerous independent domain contexts representing isolated functions running over standard localhost environments currently:

- **API Gateway**: Provides protected boundary proxy (Port: `8080`)
- **Authentication Service**: Manages accounts/JWT issuance (Port: `8081`)
- **Patient Service**: Tracks clinical subject entities (Port: `8082`)
- **Image Service**: Stores binary CT data and metadata safely (Port: `8083`)
- **Diagnosis Service**: Orchestrates foundational AI analysis workflows (Port: `8084`)
- **Severity Service**: Ensembles logic rules (Port: `8085`)
- **Treatment Service**: Maps clinical pathways conditionally (Port: `8086`)
- **Report Service**: Aggregates PDF generation (Port: `8087`)
- **AI Engine (Python)**: Executes inference processes (Port: `8000` / `5000` depending on container configuration)
- *Monitoring Service: (Planned Sprint 7 - Port: `8088`)*
- *Dependency Analyzer Service: (Planned Sprint 7 - Port: `8089`)*

---

## Sprints & Roadmap

| Sprint | Description | Status |
|-------|-------------|--------|
| Sprint 0 | Architecture & Project Setup | ✅ Completed |
| Sprint 1 | Authentication & Authorization | ✅ Completed |
| Sprint 2 | Patient Management | ✅ Completed |
| Sprint 3 | Medical Image Service | ✅ Completed |
| Sprint 4 | AI Engine & Diagnosis Integration | ✅ Completed |
| Sprint 5 | Clinical Decision Support Integration | ✅ Completed |
| Sprint 6 | React Frontend & Backend Integration | ✅ Completed |
| Sprint 7 | Monitoring & Intelligent Microservice Dependency Analyzer | ⏳ Planned |
| Sprint 8 | Docker, Deployment, Performance & Final Documentation | ⏳ Planned |

### Sprint 6 — Completed

Sprint 6 delivered a comprehensive frontend integration successfully resolving:
- React frontend bootstrapping heavily reliant on robust JWT-aware API capabilities mapping HTTP queries seamlessly to Axios clients.
- User management GUI respecting Admin-only authorization limits successfully restricted.
- Complete Diagnosis lifecycle mapping starting from staging clinical image records, deploying to iterative prediction endpoints, capturing consistency, modeling severity, deploying treatment, all alongside identical-page presentation layers.
- Strict isolation and presentation of individual artifacts supporting Original CT visualization, Segmentation analysis renders, and Grad-CAM mapping natively.
- PDF Report clinical previews and structured secure document download funnels completely replacing static text streams.
- Extensive loading states, error boundaries, and API failover UI handlers reflecting fully integrated full-stack communications architecture properly.

### Sprint 7 — Monitoring & Intelligent Microservice Dependency Analyzer (⏳ Planned)

**Monitoring:**
- Extending existing Actuator surfaces yielding granular service health, availability, and response-time tracking endpoints seamlessly integrated into external telemetry.
- Targeted error monitoring logs visualizing resource thresholds and system-wide service statuses dynamically.

**Dependency Analyzer:**
- Centralized service dependency extraction rendering physical structural architectures visually via active dependency graphs.
- Autonomous bottleneck isolation targeting cascaded failure profiles highlighting vulnerable failure paths across domains.
- Deep root-cause detection generating reliability insights strictly mapping failure patterns logically protecting clinical service stability globally.

---

## API Documentation

Swagger OpenAPI mapping URLs deployed dynamically during local testing profiles on internal microservice origins currently mapped:
- **Authentication Service**: `http://localhost:8081/swagger-ui/index.html`
- **Patient Service**: `http://localhost:8082/swagger-ui/index.html`
- **Image Service**: `http://localhost:8083/swagger-ui/index.html`
- **Diagnosis Service**: `http://localhost:8084/swagger-ui/index.html`
- **Severity Service**: `http://localhost:8085/swagger-ui/index.html`
- **Treatment Service**: `http://localhost:8086/swagger-ui/index.html`
- **Report Service**: `http://localhost:8087/swagger-ui/index.html`

---

## Running the Project

1. **Start PostgreSQL database** (Initialize schemas aligned identically matching microservice requirements natively or via default container mappings).
2. **Start Backend Edge Microservices** ensuring API-Gateway functions properly orchestrating child configurations.
3. **Start the AI Engine**:
   ```bash
   cd ai-engine
   python -m venv venv
   source venv/Scripts/activate # Windows
   pip install -r requirements.txt
   uvicorn api.main:app --port 8000
   ```
4. **Start the Frontend Application**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
5. **Open Initial Interface Endpoint**: Access UI directly launching at `http://localhost:3000`.

---

## Security Protocols

- Universal **JWT-based Bearer Authentication** actively securing intra-service communication enforcing standard filtering constraints traversing the Gateway correctly.
- Granular edge profiles rely on verified **Spring Security** mechanisms enforcing **BCrypt algorithm mappings** strictly validating hashed secret instances securely.
- Role-based authorization layers limiting image interactions proactively to administrative tiers.

---

## Database 

Central database mapping persists locally strictly operating across integrated local **PostgreSQL 15** deployments natively.

---

## Limitations & Disclaimer ⚠️

**KidneyStoneAI is strictly an AI-assisted clinical decision-support and academic research system.** 
Its predictions, classifications, AI logic rendering, and generated clinical reporting outputs should *not* be treated as definitive medical diagnosis, diagnostic certitude, or direct treatment mapping prescription. Clinical decisions, diagnostic observations, and patient-centric implementations must strictly be initiated manually by qualified, trained healthcare professionals operating safely within controlled hospital frameworks.