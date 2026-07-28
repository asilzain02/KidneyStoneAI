# PROJECT_MANIFEST.md

# AI Project Memory & Progress Tracker

Version: 1.0.0

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

Sprint 0 Scaffolding Complete

Completion

5%

Current Milestone

Repository Initialization

Current Sprint

Sprint 1 — COMPLETE

Next Sprint

Sprint 2 — Patient Service Implementation

Project Health

Healthy

Last Updated

2026-07-28

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

Status

Complete

Patient Service

Pending

Image Service

Pending

Diagnosis Service

Pending

Segmentation Service

Pending

Severity Service

Pending

Treatment Service

Pending

Report Service

Pending

Monitoring Service

Pending

Dependency Analyzer

Pending

Frontend

Pending

Database

Pending

Docker

Pending

Testing

Pending

Deployment

Pending

Documentation

Planning

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

Sprint 2 — Patient Service Implementation

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

0

Endpoints Implemented

0

Endpoints Tested

0

Swagger

Not Started

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

Pending

BCrypt

Pending

Role Based Access

Pending

HTTPS Ready

Pending

Input Validation

Pending

Exception Handling

Pending

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

Version

1.2.0 — 2026-07-28

Changes

Sprint 1 Complete

Implemented Authentication Service including Flyway PostgreSQL migrations, JWT/BCrypt security, Entities, Repositories, DTOs, Mappers, Services, Controllers, validation, Swagger UI and tests.

Sprint 0.1 Complete

Renamed 'rullebook' folder to 'rulebook' and corrected all documentation references.

Fixed AI Stack documentation to correctly reference 'Ultralytics YOLO11'.

Updated Severity Module documentation to use 'Ensemble Severity Prediction'.

Added Redis, RabbitMQ, MinIO, Loki, and Promtail to docker-compose.yml and .env.example.

Created backend/shared library for Common DTOs, Exceptions, Utilities, Constants, and Configuration.

Added OpenAPI Code Generator configuration to parent pom.xml.

Added basic GitHub Actions CI pipeline (.github/workflows/build.yml).

Upgraded PostgreSQL image from version 15 to 16 in docker-compose.yml.

Sprint 0 Complete

Complete folder structure scaffolded per ARCHITECTURE.md Section 3

All 10 backend microservice Maven projects initialized

All service application.yml configs generated

All service Dockerfiles generated (multi-stage, non-root)

Python AI Engine requirements.txt + Dockerfile generated

React frontend package.json + tsconfig.json + Dockerfile generated

All 9 PostgreSQL schema SQL files generated per DATABASE.md

docker-compose.yml generated with full service mesh + health checks

Prometheus scrape config generated for all services

README.md generated

Inconsistency noted: root folder is named 'rullebook' (typo), Architecture.md specifies 'rulebook'. Preserved to avoid breaking existing references.

---

# CURRENT TASK

Sprint 1 Complete — Begin Sprint 2

Next Task

Implement Patient Service (entities, repository, service, controller)

---

# NEXT FIVE TASKS

1

Implement Authentication Service — Sprint 1

2

Implement Patient Service — Sprint 2

3

Implement Image Service — Sprint 3

4

Implement Diagnosis Service + AI Engine Integration — Sprint 4

5

Implement Frontend Login + Dashboard — Sprint 5

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