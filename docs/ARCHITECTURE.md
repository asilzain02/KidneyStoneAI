Section 1 – System Architecture & Design Principles

# ARCHITECTURE.md

Project Name

AI-Powered Reliable Clinical Decision Support Platform for Kidney Stone Diagnosis Using Explainable AI and Intelligent Microservice Dependency Analysis

Version

1.0

---

# PURPOSE

This document defines the complete architecture of the system.

Every implementation, feature, API, database design, AI model, frontend component, and deployment must follow this architecture.

Architecture modifications must be documented before implementation.

This architecture is the single source of truth for the project.

---

# SYSTEM VISION

The objective is to build a production-grade AI Healthcare Platform capable of:

• Detecting kidney stones from CT scans

• Segmenting kidney stones

• Assessing disease severity

• Generating treatment recommendations

• Producing explainable AI visualizations

• Monitoring the health of all AI services

• Predicting cascading failures between services

The system must remain:

✓ Modular

✓ Scalable

✓ Secure

✓ Maintainable

✓ Fault Tolerant

✓ Docker Deployable

---

# ARCHITECTURE STYLE

Primary Architecture

Microservices Architecture

Design Pattern

Clean Architecture

Communication

REST APIs

Deployment

Docker Compose

Authentication

JWT

Database

PostgreSQL

AI

Python

---

# HIGH LEVEL ARCHITECTURE

                 Doctor/Admin

                       │

               React Frontend

                       │

               API Gateway

                       │

------------------------------------------------------

Authentication Service

Patient Service

Image Service

Diagnosis Service

Severity Service

Treatment Service

Report Service

Monitoring Service

Dependency Analyzer Service

------------------------------------------------------

                       │

                PostgreSQL Database

                       │

                 Python AI Engine

------------------------------------------------------

Ultralytics YOLO11

U-Net

GradCAM

Severity Model

Failure Prediction Model

------------------------------------------------------

---

# SYSTEM LAYERS

Layer 1

Presentation Layer

React

Purpose

Doctor Dashboard

Patient Dashboard

Admin Dashboard

Authentication

Reports

---

Layer 2

API Layer

Spring Cloud Gateway

Purpose

Single Entry Point

Authentication

Routing

Rate Limiting

Security

---

Layer 3

Business Layer

Spring Boot Microservices

Each service owns one business domain.

Never mix business logic.

---

Layer 4

AI Layer

Python

Responsible for

Image Processing

Detection

Segmentation

Severity Prediction

Explainability

---

Layer 5

Persistence Layer

PostgreSQL

Stores

Patients

Predictions

Clinical Data

Reports

Monitoring Metrics

---

Layer 6

Infrastructure Layer

Docker

Prometheus

NetworkX

Logging

Monitoring

---

# DESIGN PRINCIPLES

Always Follow

SOLID

Clean Architecture

Single Responsibility

Loose Coupling

High Cohesion

Dependency Injection

DRY

KISS

Open Closed Principle

Interface Segregation

Never violate these principles.

---

# SYSTEM CHARACTERISTICS

Modular

YES

Scalable

YES

Containerized

YES

Cloud Ready

YES

Fault Tolerant

YES

Secure

YES

Maintainable

YES

Production Ready

YES

---

# PRIMARY USERS

Doctor

Upload CT Scan

Review Diagnosis

Generate Reports

View Explainability

Administrator

Manage Users

Monitor Services

View Dependency Graph

View System Health

Patient

(Optional)

View Reports

Medical History

---

# SYSTEM WORKFLOW

Doctor Login

↓

Patient Selection

↓

Upload CT Scan

↓

Image Validation

↓

AI Detection

↓

Stone Segmentation

↓

Feature Extraction

↓

Severity Prediction

↓

Treatment Recommendation

↓

GradCAM

↓

Generate Report

↓

Store Result

↓

Return Dashboard

---

# SERVICE COMMUNICATION

React

↓

Gateway

↓

Authentication

↓

Patient

↓

Image

↓

Diagnosis

↓

Severity

↓

Treatment

↓

Report

Every communication happens through REST APIs.

No service directly accesses another service's database.

---

# DATABASE STRATEGY

One PostgreSQL instance

Multiple schemas

Authentication Schema

Patient Schema

Diagnosis Schema

Monitoring Schema

Future Ready

Can later migrate to database-per-service architecture.

---

# SCALABILITY STRATEGY

Every microservice must be independently scalable.

If Diagnosis Service receives heavy traffic,

only Diagnosis Service should be replicated.

Never scale the entire application unnecessarily.

---

# FAULT TOLERANCE

If Report Service fails

Diagnosis continues.

If Monitoring Service fails

Prediction continues.

If Dependency Analyzer fails

Healthcare workflow continues.

Critical services should never depend on monitoring services.

---

# AI PIPELINE

CT Scan

↓

Preprocessing

↓

YOLO Detection

↓

Stone Localization

↓

U-Net Segmentation

↓

Stone Measurements

↓

Severity Prediction

↓

Treatment Recommendation

↓

GradCAM

↓

Return Prediction

---

# DEPENDENCY ANALYZER PIPELINE

Collect Metrics

↓

Collect Health Status

↓

Build Dependency Graph

↓

Detect Bottlenecks

↓

Predict Cascading Failures

↓

Identify Root Cause

↓

Generate Dashboard

---

# NON FUNCTIONAL GOALS

Prediction Time

Less than 5 Seconds

Availability

99%

Maintainability

High

Security

High

Scalability

High

Reliability

High

Extensibility

High

---

# ARCHITECTURE RULES

Never bypass API Gateway.

Never bypass Service Layer.

Never allow frontend to access database.

Never expose AI Engine directly.

Never expose internal APIs publicly.

Always authenticate requests.

Always validate input.

Always log important events.

Always document APIs.

Always update Architecture.md before making architectural changes.

---

            END OF SECTION 1


                    Section 2 — Microservice Architecture

# ============================================================
# SECTION 2 — MICROSERVICE ARCHITECTURE
# ============================================================

## OBJECTIVE

The platform follows Domain-Driven Microservices.

Each service owns a single business capability.

Each service:

- has its own controller
- has its own service layer
- has its own repository
- has its own entities
- has its own DTOs
- has its own exceptions
- has its own APIs
- has its own validation
- has its own business logic

Never mix responsibilities.

Never create God Services.

------------------------------------------------------------

# COMPLETE SERVICE MAP

                    React Frontend

                           │

                    API Gateway

                           │

--------------------------------------------------------------

Authentication Service

Patient Service

Image Service

Diagnosis Service

Severity Service

Treatment Service

Report Service

Monitoring Service

Dependency Analyzer Service

Notification Service (Future)

--------------------------------------------------------------

                     PostgreSQL

--------------------------------------------------------------

                   Python AI Engine

--------------------------------------------------------------

Ultralytics YOLO11

U-Net

GradCAM

Severity Model

Failure Prediction Model

--------------------------------------------------------------

# SERVICE COMMUNICATION

Authentication

↓

Gateway

↓

Patient

↓

Image

↓

Diagnosis

↓

Severity

↓

Treatment

↓

Report

Monitoring

↓

Dependency Analyzer

------------------------------------------------------------

# AUTHENTICATION SERVICE

Purpose

Authentication

Authorization

JWT

Role Management

Responsibilities

User Login

User Registration

JWT Token Generation

Password Encryption

Role Validation

Refresh Token

Logout

Tables

Users

Roles

Permissions

RefreshToken

Folder Structure

controller

service

repository

entity

dto

security

config

exception

util

mapper

Never store plain passwords.

Always use BCrypt.

------------------------------------------------------------

# PATIENT SERVICE

Purpose

Patient Management

Responsibilities

Create Patient

Update Patient

Delete Patient (Soft Delete)

Search Patient

Medical History

Clinical Information

Tables

Patient

ClinicalHistory

MedicalRecord

EmergencyContact

This service owns all patient information.

No other service can modify patient data.

------------------------------------------------------------

# IMAGE SERVICE

Purpose

Image Storage

Responsibilities

Upload CT Scan

Validate Image

Compress Image

Generate Metadata

Store Image

Retrieve Image

Delete Image

Tables

ImageMetadata

ImageAudit

Images stored

File System

uploads/

Future

Object Storage

Never store images inside PostgreSQL.

------------------------------------------------------------

# DIAGNOSIS SERVICE

Purpose

AI Detection

Responsibilities

Receive Image

Call Python AI

Receive Prediction

Store Detection Result

Generate Confidence Score

Tables

Prediction

Detection

Confidence

DiagnosisHistory

Communication

REST API

Python AI Engine

Never implement AI inside Java.

Java only orchestrates.

------------------------------------------------------------

# SEVERITY SERVICE

Purpose

Severity Prediction

Responsibilities

Receive AI Features

Receive Clinical Features

Predict Severity

Store Severity

Severity Levels

Low

Moderate

High

Critical

Tables

Severity

SeverityHistory

------------------------------------------------------------

# TREATMENT SERVICE

Purpose

Clinical Recommendation

Responsibilities

Recommend Hydration

Recommend Medication

Recommend ESWL

Recommend URS

Recommend PCNL

Store Recommendation

Tables

TreatmentRecommendation

TreatmentHistory

Rules Engine

Evidence Based

Never hardcode treatment rules inside controllers.

------------------------------------------------------------

# REPORT SERVICE

Purpose

Generate Reports

Responsibilities

Generate PDF

Generate JSON

Generate HTML Report

Export Reports

Tables

Report

AuditLog

Reports include

Patient

Stone Count

Stone Size

Stone Location

Severity

Treatment

GradCAM

Confidence

------------------------------------------------------------

# MONITORING SERVICE

Purpose

Runtime Monitoring

Responsibilities

Collect CPU

Collect Memory

Collect Latency

Collect Errors

Collect Response Time

Collect Service Health

Data Source

Spring Boot Actuator

Prometheus

Tables

ServiceMetrics

HealthMetrics

PerformanceHistory

------------------------------------------------------------

# DEPENDENCY ANALYZER SERVICE

Purpose

Research Contribution

Responsibilities

Discover Service Dependencies

Generate Dependency Graph

Detect Bottlenecks

Predict Cascading Failure

Predict Root Cause

Generate Risk Score

Generate Dependency Dashboard

Tables

DependencyGraph

DependencyHistory

FailurePrediction

RiskAssessment

RootCause

Uses

NetworkX

Random Forest

Never manually define dependencies.

Dependencies must be learned automatically.

------------------------------------------------------------

# PYTHON AI ENGINE

Purpose

Medical AI

Contains

Ultralytics YOLO11

U-Net

GradCAM

Image Processing

Feature Extraction

Inference API

The Python Engine exposes REST APIs.

Java consumes those APIs.

Never mix AI code into Spring Boot.

------------------------------------------------------------

# API GATEWAY

Responsibilities

Authentication

Routing

Rate Limiting

Request Validation

Security

Logging

Gateway is the ONLY public entry point.

Frontend must never communicate directly with services.

------------------------------------------------------------

# DATABASE OWNERSHIP

Authentication

Owns

Users

Roles

Permissions

Patient Service

Owns

Patient

Medical History

Image Service

Owns

Image Metadata

Diagnosis Service

Owns

Prediction

Detection

Severity Service

Owns

Severity

Treatment Service

Owns

Treatment

Report Service

Owns

Reports

Monitoring Service

Owns

Metrics

Dependency Analyzer

Owns

Dependency Graph

Failure Prediction

Never violate ownership.

------------------------------------------------------------

# SERVICE COMMUNICATION RULES

Use REST

JSON

DTOs

Validation

Never share entities.

Never expose database models.

Never bypass APIs.

Always communicate through Gateway or internal REST APIs.

------------------------------------------------------------

# INTERNAL LAYER ARCHITECTURE

Every Spring Boot Service

Controller

↓

Service

↓

Repository

↓

PostgreSQL

Controller

No business logic.

Service

Business Rules.

Repository

Database only.

Entity

Database Models.

DTO

API Models.

Mapper

Conversion.

Exception

Global Error Handling.

Security

JWT.

Configuration

Spring Configuration.

------------------------------------------------------------

# DEPLOYMENT ORDER

PostgreSQL

↓

Authentication

↓

Gateway

↓

Patient

↓

Image

↓

Diagnosis

↓

Severity

↓

Treatment

↓

Report

↓

Monitoring

↓

Dependency Analyzer

↓

Frontend

------------------------------------------------------------

# DESIGN RULES

Never combine services.

Never expose internal databases.

Never duplicate business logic.

Never bypass service layer.

Never bypass gateway.

Never allow cyclic dependencies.

Keep services loosely coupled.

Keep APIs stable.

Every service must be independently testable.

Every service must be independently deployable.

Every service must have Swagger documentation.

Every service must expose:

/health

/info

/metrics

                            END OF SECTION 2

                        Section 3 – Complete Project Folder Structure

# ============================================================
# SECTION 3 — COMPLETE PROJECT FOLDER STRUCTURE
# ============================================================

## OBJECTIVE

The project must follow a clean, modular, scalable folder structure.

Every generated file must be placed in its correct location.

Never create random folders.

Never duplicate functionality.

Every module should have a predictable location.

------------------------------------------------------------

# ROOT PROJECT STRUCTURE

KidneyStoneAI/

│

├── backend/

├── frontend/

├── ai-engine/

├── database/

├── docker/

├── docs/

├── datasets/

├── scripts/

├── deployment/

├── monitoring/

├── testing/

├── logs/

├── rulebook/

├── diagrams/

├── .gitignore

├── docker-compose.yml

├── README.md

------------------------------------------------------------

# BACKEND STRUCTURE

backend/

│

├── api-gateway/

├── authentication-service/

├── patient-service/

├── image-service/

├── diagnosis-service/

├── severity-service/

├── treatment-service/

├── report-service/

├── monitoring-service/

├── dependency-analyzer-service/

------------------------------------------------------------

# STANDARD SPRING BOOT STRUCTURE

Every service MUST follow this layout.

service-name/

│

src/

│

main/

│

java/

│

com/

│

kidneystone/

│

service/

│

controller/

│

service/

│

repository/

│

entity/

│

dto/

│

mapper/

│

config/

│

security/

│

exception/

│

util/

│

validation/

│

constant/

│

client/

│

event/

│

scheduler/

│

resources/

│

application.yml

│

application-dev.yml

│

application-prod.yml

│

static/

│

templates/

│

test/

│

Dockerfile

│

pom.xml

------------------------------------------------------------

# FRONTEND STRUCTURE

frontend/

│

public/

│

src/

│

assets/

│

components/

│

common/

│

layout/

│

pages/

│

Doctor/

│

Admin/

│

Patient/

│

hooks/

│

services/

│

context/

│

router/

│

utils/

│

constants/

│

types/

│

styles/

│

config/

│

App.tsx

│

main.tsx

│

package.json

------------------------------------------------------------

# COMPONENT STRUCTURE

components/

│

Button/

Card/

Table/

Modal/

Navbar/

Sidebar/

Loader/

Alert/

Form/

ImageViewer/

PredictionCard/

HeatmapViewer/

------------------------------------------------------------

# PAGE STRUCTURE

pages/

│

Login/

Dashboard/

Patients/

Upload/

Prediction/

Reports/

Monitoring/

DependencyGraph/

Profile/

Settings/

------------------------------------------------------------

# AI ENGINE STRUCTURE

ai-engine/

│

api/

│

models/

│

training/

│

prediction/

│

datasets/

│

weights/

│

gradcam/

│

segmentation/

│

preprocessing/

│

postprocessing/

│

evaluation/

│

feature_extraction/

│

severity/

│

treatment/

│

utils/

│

config/

│

tests/

│

requirements.txt

------------------------------------------------------------

# MODEL STRUCTURE

models/

│

yolo/

│

unet/

│

random_forest/

│

gradcam/

------------------------------------------------------------

# TRAINING STRUCTURE

training/

│

train_yolo.py

train_unet.py

train_severity.py

train_failure_prediction.py

------------------------------------------------------------

# PREDICTION STRUCTURE

prediction/

│

predict.py

detect.py

segment.py

severity.py

treatment.py

heatmap.py

------------------------------------------------------------

# DATASET STRUCTURE

datasets/

│

raw/

processed/

train/

validation/

test/

annotations/

clinical_data/

metadata/

README.md

------------------------------------------------------------

# DATABASE STRUCTURE

database/

│

schema/

migration/

seed/

backup/

erd/

------------------------------------------------------------

# SCHEMA

schema/

authentication.sql

patient.sql

image.sql

diagnosis.sql

severity.sql

treatment.sql

report.sql

monitoring.sql

dependency.sql

------------------------------------------------------------

# DOCKER STRUCTURE

docker/

│

backend/

frontend/

database/

prometheus/

python/

nginx/

------------------------------------------------------------

# DEPLOYMENT STRUCTURE

deployment/

│

development/

staging/

production/

------------------------------------------------------------

# DOCUMENTATION STRUCTURE

docs/

│

Architecture.md

Database.md

API_SPEC.md

Roadmap.md

Security.md

Testing.md

Deployment.md

DeveloperGuide.md

UserManual.md

------------------------------------------------------------

# RULEBOOK STRUCTURE

rulebook/

│

AI_RULEBOOK.md

PROJECT_MANIFEST.md

PROMPT_LIBRARY.md

CODING_STANDARD.md

------------------------------------------------------------

# TESTING STRUCTURE

testing/

│

unit/

integration/

api/

performance/

security/

------------------------------------------------------------

# LOG STRUCTURE

logs/

│

backend/

frontend/

python/

docker/

------------------------------------------------------------

# CONFIGURATION FILES

Never hardcode configuration.

Use

.env

application.yml

application-dev.yml

application-prod.yml

------------------------------------------------------------

# FILE NAMING CONVENTIONS

Java Classes

PascalCase

Example

PatientController

DiagnosisService

PredictionRepository

------------------------------------------------------------

Variables

camelCase

Example

patientId

predictionResult

confidenceScore

------------------------------------------------------------

Constants

UPPER_CASE

Example

JWT_SECRET

MAX_FILE_SIZE

------------------------------------------------------------

Packages

lowercase

Example

controller

service

repository

------------------------------------------------------------

React Components

PascalCase

PredictionCard.tsx

HeatmapViewer.tsx

------------------------------------------------------------

Hooks

use*

Example

useAuth.ts

usePatient.ts

------------------------------------------------------------

API Services

patientService.ts

diagnosisService.ts

authService.ts

------------------------------------------------------------

Python Files

snake_case

Example

predict.py

train_yolo.py

feature_extraction.py

------------------------------------------------------------

IMAGE STORAGE

Never store images inside PostgreSQL.

Store

uploads/

Only metadata inside database.

------------------------------------------------------------

MODEL STORAGE

weights/

yolo_best.pt

unet_best.pt

severity.pkl

failure_prediction.pkl

Never commit large weights to GitHub.

------------------------------------------------------------

LOG STORAGE

Every service writes logs independently.

Never mix logs.

------------------------------------------------------------

RULES

Never create folders without purpose.

Never mix frontend and backend code.

Never mix AI code with Java.

Never duplicate utilities.

Never store datasets inside backend.

Never store trained models inside source code.

Never store secrets inside repository.

Maintain identical structure across all Spring Boot services.

                            END OF SECTION 3

                        