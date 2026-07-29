# PROJECT_MANIFEST.md

# AI Project Memory & Progress Tracker

Version: v0.3

Project Name:
AI-Powered Reliable Clinical Decision Support Platform for Kidney Stone Diagnosis Using Explainable AI and Intelligent Microservice Dependency Analysis

---

# PURPOSE

This document serves as the permanent memory of the project.

Before generating any code, modifying any file, refactoring, or implementing a new feature, always read this document first.

This document must always reflect the latest project state.

Never regenerate completed modules.

Never duplicate completed work.

Only modify modules affected by the requested feature.

---

# PROJECT STATUS

Project State

Sprint 3 Complete

Completion

~42%

Current Milestone

Image Service Implementation

Current Sprint

Sprint 3 — COMPLETE

Next Sprint

Sprint 4 — Diagnosis Service Implementation

Project Health

Healthy

Last Updated

2026-07-29

---

# CURRENT VERSION

Architecture Version

1.0

Database Version

1.0

API Version

1.0

Frontend Version

0.0

Backend Version

0.0

AI Version

0.0

Dependency Analyzer Version

0.0

Docker Version

0.0

Documentation Version

1.0

---

# TECHNOLOGY STACK

Frontend

React

TypeScript

Tailwind CSS

Axios

React Router

Recharts

Backend

Java 21

Spring Boot

Spring Security

Spring Cloud Gateway

OpenFeign

JWT

Swagger

Lombok

Spring Boot Actuator

Database

PostgreSQL

AI

Python

PyTorch

Ultralytics YOLO11

U-Net

GradCAM

OpenCV

Scikit-learn

Pandas

NumPy

Monitoring

Prometheus

NetworkX

Docker

Docker Compose

Git

GitHub

---

# MODULE STATUS

Authentication Service

Status: Complete — JWT auth, BCrypt, register/login/refresh, Swagger

Patient Service

Status: Complete — CRUD, search, audit, soft-delete, Swagger, tests

Image Service

Status: Complete — upload PNG/JPG/JPEG/DICOM, local storage, metadata DB, download, soft-delete, JWT, Swagger, tests

Diagnosis Service

Status: Pending

Severity Service

Status: Pending

Treatment Service

Status: Pending

Report Service

Status: Pending

Monitoring Service

Status: Pending

Dependency Analyzer

Status: Pending

Frontend

Status: Pending

Database

Status: auth schema ✓, patient schema ✓, image schema ✓

Docker

Status: Pending

Testing

Status: Unit + Integration tests for auth, patient, and image services ✓

Deployment

Status: Pending

Documentation

Status: README updated, Manifest updated

---

# COMPLETED FEATURES

Sprint 0

Project folder structure created

Root .gitignore generated

docker-compose.yml generated (all 11 services)

.env.example generated

Root Maven parent pom.xml generated

All 10 Spring Boot service pom.xml files generated

All 10 service application.yml files generated

All 10 service Dockerfiles generated (multi-stage)

Python AI Engine Dockerfile generated

Python requirements.txt generated

Frontend package.json generated

Frontend tsconfig.json generated

Frontend Dockerfile + nginx.conf generated

All 9 database schema SQL files generated

Prometheus config generated

README.md generated

All .gitkeep placeholder files added

---

# IN PROGRESS

Sprint 4 — Diagnosis Service Implementation (Next)

---

# PENDING FEATURES

Patient Management

CT Upload

Stone Detection

Stone Segmentation

Severity Assessment

Treatment Recommendation

GradCAM

PDF Report

Dependency Discovery

Health Monitoring

Failure Prediction

Root Cause Analysis

Dashboard

Docker Deployment

Testing

Documentation

---

# DIRECTORY STRUCTURE

KidneyStoneAI/

backend/

frontend/

ai-engine/

docker/

datasets/

docs/

rulebook/

scripts/

research/

diagrams/

tests/

deployment/

---

# ACTIVE SERVICES

Currently

Redis

RabbitMQ

MinIO

Loki

Promtail

Future

Authentication

Patient

Image

Diagnosis

Severity

Treatment

Report

Monitoring

Dependency Analyzer

Gateway

---

# DATABASE STATUS

Design Started

No

Schema Completed

No

Tables Created

0

Relationships Created

0

Indexes Created

0

---

# API STATUS

Endpoints Designed

~20 (auth + patient + image)

Endpoints Implemented

~20

Endpoints Tested

~20 (unit + integration)

Swagger

Complete for Auth (8081), Patient (8082), Image (8083)

---

# FRONTEND STATUS

Login

Pending

Dashboard

Pending

Patient Module

Pending

Upload Module

Pending

Prediction Page

Pending

Reports

Pending

Admin Dashboard

Pending

---

# AI STATUS

Dataset Selected

Pending

Dataset Downloaded

Pending

Preprocessing

Pending

Training

Pending

Evaluation

Pending

Optimization

Pending

GradCAM

Pending

Deployment

Pending

---

# DEPENDENCY ANALYZER STATUS

Dependency Graph

Pending

Monitoring

Pending

Metrics Collection

Pending

Failure Prediction

Pending

Root Cause Analysis

Pending

Dashboard

Pending

---

# SECURITY STATUS

JWT

Complete — all 3 services

BCrypt

Complete — Auth Service

Role Based Access

Complete — ROLE_ADMIN, ROLE_DOCTOR on all endpoints

HTTPS Ready

Pending (will configure at Docker/reverse-proxy layer)

Input Validation

Complete — @Valid, ImageFileValidator, extension + content-type + size checks

Exception Handling

Complete — GlobalExceptionHandler (shared), ImageExceptionHandler

---

# TEST STATUS

Unit Testing

Pending

Integration Testing

Pending

API Testing

Pending

Load Testing

Pending

Security Testing

Pending

---

# DOCUMENT STATUS

README

Pending

Architecture

Pending

Database

Pending

API Specification

Pending

Security

Pending

Roadmap

Pending

Deployment Guide

Pending

Developer Guide

Pending

---

# CHANGELOG

v0.3 — 2026-07-29

Changes

Sprint 3 Complete

Implemented Image Service: MedicalImage entity (BaseEntity), Flyway migration (image schema), FileStorageService interface + LocalFileStorageService implementation, ImageFileValidator (extension/content-type/size), ImageService, ImageController (5 endpoints), ImageMapper (MapStruct), ImageExceptionHandler, JWT security (JwtProvider, JwtAuthenticationFilter, SecurityConfig), ImageServiceConfig (OpenAPI + JPA Auditing), unit tests (ImageServiceTest, ImageFileValidatorTest), integration tests (ImageControllerIntegrationTest). README.md extended. PROJECT_MANIFEST.md updated.

JWT Architecture Redesign (Hotfix)

Redesigned JWT structure to serialize authorities as a List of Strings under the "authorities" claim (replacing "role" claim). BaseJwtProvider extracted to the shared library for Future-Proofing (consumed by auth, patient, and image services). JwtAuthenticationFilter regex extraction removed in favor of Stream mapping into SimpleGrantedAuthority, resolving the 403 Forbidden flaw. H2 TestPropertySource configs hardened across patient and auth integration tests to allow perfect decoupled pipeline executions without Docker daemon dependence.

v0.2 — 2026-07-28

Sprint 2 Complete

Implemented Patient Service (CRUD, search, audit, soft-delete, Swagger, tests).

v0.1 — 2026-07-28

Sprint 1 Complete

Implemented Authentication Service including Flyway PostgreSQL migrations, JWT/BCrypt security, Entities, Repositories, DTOs, Mappers, Services, Controllers, validation, Swagger UI and tests.

Sprint 0.1 Complete

Renamed 'rullebook' folder to 'rulebook' and corrected all documentation references.

Created backend/shared library for Common DTOs, Exceptions, Utilities, Constants, and Configuration.

Sprint 0 Complete

Complete folder structure scaffolded. All 10 backend microservice Maven projects initialized. All service configs, Dockerfiles, DB schemas, docker-compose.yml, Prometheus config, and README generated.

---

# CURRENT TASK

Sprint 3 Complete — Begin Sprint 4

Next Task

Implement Diagnosis Service (AI integration — calls Python AI Engine)

---

# NEXT FIVE TASKS

1

Implement Diagnosis Service — Sprint 4 (OpenFeign call to Python AI Engine)

2

Implement Severity Service — Sprint 5

3

Implement Treatment Service — Sprint 6

4

Implement Report Service — Sprint 7

5

Implement Frontend Login + Dashboard — Sprint 9

---

# RULES FOR AI

Always read this file before coding.

Never regenerate completed modules.

Never delete completed features.

Never rename folders without updating documentation.

Never modify architecture without updating Architecture.md.

Never modify APIs without updating API_SPEC.md.

Never modify database without updating DATABASE.md.

Never modify security without updating SECURITY.md.

Always update this manifest after every completed task.

Always preserve backward compatibility.

Never introduce breaking changes without documenting them.

Always record completed milestones.

---

# DEFINITION OF DONE

A task is considered complete only if:

Code Compiles

Tests Pass

Documentation Updated

Manifest Updated

API Updated

Docker Compatible

Secure

Reviewed

---

END OF MANIFEST