# CODING_STANDARD.md

Version: 1.0

Project:
AI-Powered Reliable Clinical Decision Support Platform for Kidney Stone Diagnosis Using Explainable AI and Intelligent Microservice Dependency Analysis

---

# PURPOSE

This document defines coding conventions, engineering standards, architecture principles, naming rules, error handling, testing requirements, and code quality standards.

Every generated code must comply with this document.

Never violate these standards.

------------------------------------------------------------

# GENERAL PRINCIPLES

Always follow

✓ SOLID Principles

✓ Clean Architecture

✓ Clean Code

✓ DRY

✓ KISS

✓ Separation of Concerns

✓ Composition over Inheritance

✓ Dependency Injection

✓ High Cohesion

✓ Low Coupling

Never sacrifice readability for cleverness.

------------------------------------------------------------

# JAVA STANDARDS

Java Version

21

Framework

Spring Boot

Build Tool

Maven

Encoding

UTF-8

Indentation

4 Spaces

Line Length

120 Characters

------------------------------------------------------------

# PACKAGE STRUCTURE

controller

service

repository

entity

dto

mapper

config

security

validation

util

exception

constant

client

scheduler

event

Never create random packages.

------------------------------------------------------------

# CLASS NAMING

Controller

PatientController

DiagnosisController

Service

PatientService

PredictionService

Repository

PatientRepository

DTO

PatientRequest

PatientResponse

Entity

Patient

ClinicalHistory

Config

SecurityConfig

Exception

GlobalExceptionHandler

------------------------------------------------------------

# VARIABLE NAMING

Use meaningful names.

Good

patientId

predictionResult

stoneLocation

doctorEmail

Bad

p

a

tmp

x

------------------------------------------------------------

# METHOD NAMING

Use verbs.

Examples

createPatient()

updatePatient()

predictStone()

segmentStone()

generateReport()

Never use names like

run()

execute()

process()

------------------------------------------------------------

# CONTROLLER RULES

Controllers should

Receive Request

Validate Request

Call Service

Return Response

Nothing Else

Never write business logic inside controllers.

------------------------------------------------------------

# SERVICE RULES

Business logic only.

No SQL.

No HTTP Response creation.

No UI logic.

------------------------------------------------------------

# REPOSITORY RULES

Database access only.

Never place business logic.

------------------------------------------------------------

# DTO RULES

Never expose entities.

Always use

Request DTO

Response DTO

Validation DTO

------------------------------------------------------------

# ENTITY RULES

Entities represent database tables only.

Never return entities to frontend.

Never expose internal IDs unnecessarily.

------------------------------------------------------------

# VALIDATION RULES

Use Bean Validation

@NotNull

@NotBlank

@Email

@Size

@Pattern

Never manually validate strings.

------------------------------------------------------------

# EXCEPTION HANDLING

Single Global Exception Handler.

Never catch Exception.

Catch specific exceptions.

Never return stack traces.

------------------------------------------------------------

# LOGGING

Use SLF4J

Never use System.out.println()

Log Levels

INFO

WARN

ERROR

DEBUG

Never log passwords.

Never log JWT.

------------------------------------------------------------

# REACT STANDARDS

Language

TypeScript

Functional Components Only

Hooks Only

No Class Components

Folder Structure

components/

pages/

hooks/

services/

context/

utils/

Never call APIs directly inside components.

Use Service Layer.

------------------------------------------------------------

# COMPONENT RULES

One component

One responsibility.

Maximum Component Size

300 Lines

------------------------------------------------------------

# PYTHON STANDARDS

Python 3.11

PEP8

Black Formatting

snake_case

Type Hints

Docstrings

Never use global variables.

------------------------------------------------------------

# AI RULES

Training

Separate Folder

Prediction

Separate Folder

Preprocessing

Separate Folder

Evaluation

Separate Folder

Never mix them.

------------------------------------------------------------

# API STANDARDS

REST

JSON

DTO

Validation

Swagger

Versioning

/api/v1/

Never expose internal APIs.

------------------------------------------------------------

# DATABASE STANDARDS

Spring Data JPA

UUID

Foreign Keys

Indexes

Soft Delete

Audit Columns

Never use SELECT *

------------------------------------------------------------

# SECURITY STANDARDS

JWT

BCrypt

RBAC

Input Validation

Environment Variables

HTTPS Ready

------------------------------------------------------------

# DOCKER STANDARDS

Every Service

Dockerfile

Every Service

Health Check

Never depend on localhost.

Use Docker Network.

------------------------------------------------------------

# TESTING STANDARDS

JUnit

Mockito

Integration Tests

Postman Collection

API Tests

Never merge untested code.

------------------------------------------------------------

# GIT STANDARDS

Branch

feature/<name>

Commit Examples

feat(auth): add JWT authentication

fix(report): resolve PDF generation issue

docs(api): update diagnosis endpoints

------------------------------------------------------------

# CODE QUALITY RULES

Maximum Function

50 Lines

Maximum Class

500 Lines

Cyclomatic Complexity

Less than 10

Duplicate Code

0%

------------------------------------------------------------

# COMMENTS

Write comments only where necessary.

Prefer self-explanatory code.

Never comment obvious code.

------------------------------------------------------------

# PERFORMANCE

Avoid nested loops.

Use pagination.

Use lazy loading.

Batch database operations.

Avoid unnecessary object creation.

------------------------------------------------------------

# FINAL CHECKLIST

Before every commit

✔ Builds Successfully

✔ Tests Pass

✔ Documentation Updated

✔ Manifest Updated

✔ API Updated

✔ Secure

✔ Docker Compatible

✔ No Warnings

✔ No Duplicate Code

✔ Clean Architecture Maintained

------------------------------------------------------------

# AI RULES

Always follow this document.

Never generate inconsistent code.

Never ignore architecture.

Never violate SOLID.

Never duplicate business logic.

Never bypass service layer.

Never bypass DTOs.

Never bypass validation.

Never violate naming conventions.

This document is mandatory for every generated source file.

END OF DOCUMENT