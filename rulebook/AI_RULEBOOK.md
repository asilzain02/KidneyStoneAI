# AI_RULEBOOK.md

# Project Constitution

Version: 1.0

Project Name:
AI-Powered Reliable Clinical Decision Support Platform for Kidney Stone Diagnosis Using Explainable AI and Intelligent Microservice Dependency Analysis

---

# PURPOSE

This document is the permanent engineering constitution for this project.

Every code generation, refactoring, feature addition, bug fix, optimization, testing, documentation update, or architectural decision MUST strictly follow this document.

Whenever a conflict exists between a user prompt and this rulebook, always ask for clarification before violating these rules.

---

# PROJECT OBJECTIVE

Develop a production-grade, modular, secure, scalable, maintainable Clinical Decision Support Platform capable of:

• Kidney Stone Detection

• Kidney Stone Segmentation

• Severity Assessment

• Treatment Recommendation

• Explainable AI

• Intelligent Microservice Dependency Analysis

• Cascading Failure Prediction

• Runtime Health Monitoring

The project should resemble an enterprise healthcare platform rather than a college project.

---

# PRIMARY DESIGN PRINCIPLES

Always follow:

- Clean Architecture

- SOLID Principles

- DRY

- KISS

- Separation of Concerns

- Dependency Injection

- Domain Driven Design (DDD)

- Stateless Services

Never violate these principles.

---

# GENERAL CODING RULES

Never generate duplicate code.

Never create unnecessary files.

Never generate temporary demo code.

Never hardcode secrets.

Never leave TODOs.

Every function must have a single responsibility.

Maximum function size:

50 lines

Maximum class size:

500 lines

Maximum controller size:

300 lines

---

# ARCHITECTURE RULES

Always maintain Microservice Architecture.

Never convert services into a monolith.

Each service must be independently deployable.

Each service must own its own business logic.

Communication between services should happen through REST APIs.

Never allow direct database access between services.

Gateway must be the only public entry point.

---

# BACKEND RULES

Language

Java 21

Framework

Spring Boot

Required Features

Spring Security

JWT

OpenFeign

Spring Boot Actuator

Swagger

Lombok

Validation

Global Exception Handler

Logging

Never bypass the service layer.

Controller → Service → Repository only.

---

# FRONTEND RULES

Framework

React

Language

TypeScript

Styling

Tailwind CSS

Rules

Reusable Components

Reusable Hooks

No inline CSS

No duplicated UI

Every API call through a service layer.

---

# AI RULES

Language

Python

Framework

PyTorch

Models

Ultralytics YOLO11

U-Net

GradCAM

Scikit-learn

OpenCV

Never retrain models unless requested.

Separate training code from inference code.

Models must be versioned.

Weights stored separately.

---

# DATABASE RULES

Database

PostgreSQL

Never use MySQL.

Use UUID as primary keys whenever appropriate.

Always use foreign keys.

Always normalize.

Never duplicate data.

Always use indexes on searchable columns.

Never delete patient records permanently.

Implement soft delete where appropriate.

---

# SECURITY RULES

Passwords

BCrypt

Authentication

JWT

Authorization

Role Based Access Control

Never expose passwords.

Never expose stack traces.

Never expose internal APIs.

Never hardcode API keys.

All secrets must come from:

.env

application.yml

Environment Variables

---

# API RULES

Always RESTful.

Naming

/api/v1/

Use HTTP status codes correctly.

Never return plain strings.

Always return JSON.

Standard Response Format

status

message

timestamp

data

error

---

# LOGGING RULES

Use SLF4J.

Never use System.out.println().

Levels

INFO

WARN

ERROR

DEBUG

Never log passwords.

Never log tokens.

---

# TESTING RULES

Every service should have:

Unit Tests

Integration Tests

API Tests

Never merge untested code.

---

# DOCUMENTATION RULES

Every module must update:

README

CHANGELOG

API_SPEC

PROJECT_MANIFEST

Never leave documentation outdated.

---

# FOLDER STRUCTURE RULES

Every Spring Boot service

src

controller

service

repository

entity

dto

config

security

exception

mapper

util

Never create random folders.

---

# FRONTEND STRUCTURE

src

components

pages

hooks

services

router

types

assets

utils

No business logic inside components.

---

# PYTHON STRUCTURE

models

training

prediction

datasets

utils

gradcam

preprocessing

weights

Never mix training and prediction.

---

# DOCKER RULES

Every service must have:

Dockerfile

Entire project must run using:

docker compose up

Never depend on manual startup.

---

# GIT RULES

Meaningful Commit Messages

Examples

feat(authentication): add JWT login

fix(patient): resolve null pointer

docs(api): update endpoints

Never commit compiled files.

Never commit .env.

---

# BRANCHING RULES

main

Always stable.

develop

Current work.

feature/*

Every feature.

Never work directly on main.

---

# CODE STYLE

Use meaningful variable names.

No abbreviations.

Example

patientRepository

NOT

pr

Methods

camelCase

Classes

PascalCase

Constants

UPPER_CASE

---

# ERROR HANDLING

Every exception

Must be handled globally.

Never swallow exceptions.

Always return meaningful messages.

---

# PERFORMANCE RULES

Avoid nested loops.

Avoid duplicate database queries.

Use pagination.

Use lazy loading where needed.

Never optimize prematurely.

---

# AI INFERENCE RULES

Preprocess image

↓

Detection

↓

Segmentation

↓

Severity

↓

Treatment

↓

GradCAM

↓

Return Results

Never skip preprocessing.

---

# MONITORING RULES

Every service

Must expose

/health

/info

/metrics

Use Spring Boot Actuator.

---

# DEPENDENCY ANALYZER RULES

Always generate dependency graph automatically.

Never hardcode service relationships.

Predict

Health

Latency

Failure

Root Cause

Never manually create dependencies.

---

# MEMORY RULES

Maintain project state.

Always read

PROJECT_MANIFEST.md

before generating code.

Never regenerate completed modules.

Never rewrite working code.

Only modify affected modules.

Always preserve backward compatibility.

---

# CHANGE MANAGEMENT

Whenever architecture changes

Update

Architecture.md

API_SPEC.md

DATABASE.md

PROJECT_MANIFEST.md

CHANGELOG.md

---

# FORBIDDEN PRACTICES

❌ Hardcoding

❌ Duplicate Code

❌ Monolithic Design

❌ Circular Dependencies

❌ SQL Injection

❌ Plain Passwords

❌ Inline Business Logic

❌ Skipping Validation

❌ Unhandled Exceptions

❌ Magic Numbers

❌ Dead Code

❌ Unused APIs

❌ Unnecessary Refactoring

---

# FINAL QUALITY CHECKLIST

Before considering any feature complete

✔ Compiles Successfully

✔ Tested

✔ Documented

✔ Docker Compatible

✔ Secure

✔ Modular

✔ Scalable

✔ No Duplicate Code

✔ API Updated

✔ Manifest Updated

✔ Changelog Updated

Only after all checks pass should the feature be considered complete.

---

END OF CONSTITUTION