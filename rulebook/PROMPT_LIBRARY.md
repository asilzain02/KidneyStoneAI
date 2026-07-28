# PROMPT_LIBRARY.md

Version 1.0

Project

AI-Powered Reliable Clinical Decision Support Platform for Kidney Stone Diagnosis Using Explainable AI and Intelligent Microservice Dependency Analysis

---

# PURPOSE

This file contains standardized prompts for Antigravity.

Every implementation should use these prompts.

Never start from scratch.

Always extend existing implementation.

Always read

AI_RULEBOOK.md

PROJECT_MANIFEST.md

ARCHITECTURE.md

DATABASE.md

API_SPEC.md

SECURITY.md

CODING_STANDARD.md

before generating code.

----------------------------------------------------------

MASTER RULE

Before writing code

Understand

Current Architecture

↓

Current Module

↓

Dependencies

↓

Affected APIs

↓

Affected Database

↓

Existing Tests

↓

Documentation

Never regenerate existing modules.

Only modify affected components.

----------------------------------------------------------

PROMPT 1

CREATE NEW MICROSERVICE

Build a complete production-ready Spring Boot microservice following all project rulebooks.

Requirements

Java 21

Spring Boot

JWT

Swagger

Validation

Exception Handling

Logging

Docker

Health Endpoint

Metrics Endpoint

OpenAPI

DTO

Mapper

Repository

Service

Controller

Return complete folder structure.

Do not skip any file.

----------------------------------------------------------

PROMPT 2

CREATE DATABASE

Generate PostgreSQL tables according to DATABASE.md.

Generate

Flyway Migration

Indexes

Constraints

Foreign Keys

Audit Columns

Soft Delete

UUID

Never invent schema.

----------------------------------------------------------

PROMPT 3

CREATE REST APIs

Implement REST APIs according to API_SPEC.md.

Never invent endpoints.

Generate

Controller

DTO

Service

Repository

Mapper

Validation

Exception Handling

Swagger Documentation

----------------------------------------------------------

PROMPT 4

BUILD FRONTEND PAGE

Build production-ready React TypeScript page.

Use

Tailwind

Axios

Reusable Components

Loading

Error State

Validation

Responsive Design

Dark Mode Support

No inline CSS.

----------------------------------------------------------

PROMPT 5

CONNECT FRONTEND

Connect frontend with backend.

Generate

Axios Service

API Calls

Error Handling

Retry

Loading State

Never hardcode URLs.

----------------------------------------------------------

PROMPT 6

BUILD AI MODULE

Generate production-ready Python module.

Follow

PEP8

Type Hint

Docstring

Logging

Configuration

Never mix training with inference.

----------------------------------------------------------

PROMPT 7

TRAIN MODEL

Generate training pipeline.

Dataset

Preprocessing

Augmentation

Training

Validation

Checkpoint

TensorBoard

Evaluation

Export Best Model

----------------------------------------------------------

PROMPT 8

BUILD INFERENCE API

Generate FastAPI inference server.

Requirements

YOLO

U-Net

GradCAM

REST API

Health Check

Docker

Logging

----------------------------------------------------------

PROMPT 9

GENERATE TESTS

Generate

JUnit

Mockito

Integration Tests

API Tests

Python Tests

Frontend Tests

Cover

Positive

Negative

Edge Cases

----------------------------------------------------------

PROMPT 10

GENERATE DOCKER

Create Dockerfile.

Follow best practices.

Multi-stage build.

Health Check.

Small image.

----------------------------------------------------------

PROMPT 11

UPDATE DOCUMENTATION

Whenever implementation changes

Update

README

Architecture

API

Manifest

Database

Changelog

Never leave documentation outdated.

----------------------------------------------------------

PROMPT 12

ADD NEW FEATURE

Implement feature without breaking existing architecture.

Update

Backend

Frontend

Database

Tests

Documentation

Manifest

----------------------------------------------------------

PROMPT 13

REFACTOR

Refactor code.

Do NOT change functionality.

Improve

Readability

Performance

Maintainability

Never introduce breaking changes.

----------------------------------------------------------

PROMPT 14

BUG FIX

Fix bug.

Explain

Root Cause

Solution

Affected Files

Regression Risk

Tests

----------------------------------------------------------

PROMPT 15

DEPENDENCY ANALYZER

Generate

Dependency Graph

Runtime Discovery

Metrics Collection

Failure Prediction

Root Cause

Risk Score

Dashboard

NetworkX

Random Forest

----------------------------------------------------------

PROMPT 16

MONITORING

Generate

Spring Boot Actuator

Prometheus

Metrics

Health

Latency

CPU

Memory

Dashboard

----------------------------------------------------------

PROMPT 17

SECURITY

Review

JWT

BCrypt

Validation

OWASP

Secrets

Authorization

Authentication

Report vulnerabilities.

----------------------------------------------------------

PROMPT 18

CODE REVIEW

Review code like Google Senior Engineer.

Check

Architecture

Security

Performance

Readability

SOLID

Scalability

Clean Code

----------------------------------------------------------

PROMPT 19

PERFORMANCE REVIEW

Analyze

Memory

CPU

Queries

API Latency

Caching

Concurrency

Suggest improvements.

----------------------------------------------------------

PROMPT 20

PROJECT STATUS

Read PROJECT_MANIFEST.md

Return

Completed

Pending

Current Task

Next Task

Affected Modules

Risk

Progress %

Never analyze unnecessary files.

----------------------------------------------------------

PROMPT 21

BEFORE EVERY IMPLEMENTATION

Always

Read Rulebook

Read Manifest

Read Architecture

Read API Spec

Read Database

Read Security

Read Coding Standard

Understand affected module.

Implement only requested feature.

Never modify unrelated code.

----------------------------------------------------------

PROMPT 22

AFTER EVERY IMPLEMENTATION

Update

PROJECT_MANIFEST.md

CHANGELOG.md

README.md

Architecture.md

API_SPEC.md

DATABASE.md

Return

Summary

Files Changed

Tests Added

Risk

Next Task

----------------------------------------------------------

PROMPT 23

FINAL QUALITY CHECK

Before declaring task complete

Verify

Build Success

Docker Success

Tests Success

No Warnings

No Duplicate Code

API Updated

Manifest Updated

Documentation Updated

Security Verified

Performance Acceptable

Return checklist.

----------------------------------------------------------

GLOBAL RULES

Never regenerate completed modules.

Never break architecture.

Never create duplicate APIs.

Never create duplicate database tables.

Never hardcode secrets.

Never change folder structure.

Never skip testing.

Never skip documentation.

Never violate AI_RULEBOOK.md.

Always think like a Senior Software Architect.

END OF DOCUMENT