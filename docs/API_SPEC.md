# API_SPEC.md

Version: 1.0

Project

AI-Powered Reliable Clinical Decision Support Platform for Kidney Stone Diagnosis Using Explainable AI and Intelligent Microservice Dependency Analysis

---

# PURPOSE

This document defines every REST API used in the project.

Every frontend request

Every backend service

Every AI call

Every internal communication

must follow this document.

Never change an endpoint without updating this document.

---

# API DESIGN PRINCIPLES

Architecture

REST

Format

JSON

Authentication

JWT

Versioning

/api/v1/

Character Encoding

UTF-8

Request

application/json

Response

application/json

---

# STANDARD RESPONSE

Every API returns

{
  "status": "SUCCESS",
  "message": "Operation completed successfully",
  "timestamp": "",
  "data": {},
  "error": null
}

Error Response

{
  "status": "ERROR",
  "message": "Validation Failed",
  "timestamp": "",
  "data": null,
  "error": {
      "code":"",
      "details":""
  }
}

---

==================================================
AUTHENTICATION SERVICE
==================================================

Base URL

/api/v1/auth

--------------------------------------------------

POST

/login

Purpose

Doctor Login

Request

{
"email":"",
"password":""
}

Response

JWT

Refresh Token

User Information

--------------------------------------------------

POST

/register

Purpose

Register Doctor/Admin

--------------------------------------------------

POST

/logout

Purpose

Logout

--------------------------------------------------

POST

/refresh-token

Purpose

Generate New Access Token

--------------------------------------------------

GET

/profile

Purpose

Current Logged User

--------------------------------------------------

PUT

/change-password

Purpose

Update Password

--------------------------------------------------

POST

/forgot-password

Purpose

Password Reset

--------------------------------------------------

POST

/reset-password

Purpose

Reset Password

--------------------------------------------------

GET

/users

Purpose

List Users

Admin Only

--------------------------------------------------

GET

/users/{id}

Purpose

User Details

--------------------------------------------------

DELETE

/users/{id}

Purpose

Soft Delete User

==================================================
PATIENT SERVICE
==================================================

Base URL

/api/v1/patients

--------------------------------------------------

POST

/

Create Patient

--------------------------------------------------

PUT

/{id}

Update Patient

--------------------------------------------------

GET

/

List Patients

Pagination Supported

--------------------------------------------------

GET

/{id}

Patient Details

--------------------------------------------------

DELETE

/{id}

Soft Delete Patient

--------------------------------------------------

GET

/search

Search Patient

--------------------------------------------------

GET

/history/{id}

Clinical History

--------------------------------------------------

POST

/history

Create Medical History

--------------------------------------------------

PUT

/history/{id}

Update Medical History

--------------------------------------------------

GET

/visits/{id}

Visit History

--------------------------------------------------

POST

/visit

Add Visit

==================================================
IMAGE SERVICE
==================================================

Base URL

/api/v1/images

--------------------------------------------------

POST

/upload

Multipart File Upload

CT Scan

--------------------------------------------------

GET

/{id}

Image Details

--------------------------------------------------

GET

/download/{id}

Download Image

--------------------------------------------------

DELETE

/{id}

Delete Image

--------------------------------------------------

GET

/patient/{patientId}

Patient Images

==================================================
DIAGNOSIS SERVICE
==================================================

Base URL

/api/v1/diagnosis

--------------------------------------------------

POST

/predict

Run Complete Diagnosis

Input

Patient ID

Image ID

Output

Prediction

--------------------------------------------------

POST

/detect

YOLO Detection

--------------------------------------------------

POST

/segment

Stone Segmentation

--------------------------------------------------

POST

/measure

Stone Measurement

--------------------------------------------------

GET

/result/{predictionId}

Prediction Result

--------------------------------------------------

GET

/history/{patientId}

Prediction History

==================================================
SEVERITY SERVICE
==================================================

Base URL

/api/v1/severity

--------------------------------------------------

POST

/predict

Severity Prediction

--------------------------------------------------

GET

/{predictionId}

Severity Details

--------------------------------------------------

GET

/history/{patientId}

Severity History

==================================================
TREATMENT SERVICE
==================================================

Base URL

/api/v1/treatment

--------------------------------------------------

POST

/recommend

Treatment Recommendation

--------------------------------------------------

GET

/{predictionId}

Treatment Details

--------------------------------------------------

PUT

/update/{id}

Doctor Override

==================================================
REPORT SERVICE
==================================================

Base URL

/api/v1/reports

--------------------------------------------------

POST

/generate

Generate Report

--------------------------------------------------

GET

/{id}

View Report

--------------------------------------------------

GET

/download/{id}

Download PDF

--------------------------------------------------

DELETE

/{id}

Delete Report

==================================================
MONITORING SERVICE
==================================================

Base URL

/api/v1/monitor

--------------------------------------------------

GET

/health

Overall Health

--------------------------------------------------

GET

/services

Service Status

--------------------------------------------------

GET

/metrics

Runtime Metrics

--------------------------------------------------

GET

/cpu

CPU Usage

--------------------------------------------------

GET

/memory

Memory Usage

--------------------------------------------------

GET

/latency

Latency

--------------------------------------------------

GET

/errors

Error Rate

==================================================
DEPENDENCY ANALYZER
==================================================

Base URL

/api/v1/dependency

--------------------------------------------------

GET

/graph

Dependency Graph

--------------------------------------------------

GET

/failures

Failure Prediction

--------------------------------------------------

GET

/root-cause

Root Cause Analysis

--------------------------------------------------

GET

/risk-score

Risk Assessment

--------------------------------------------------

GET

/bottlenecks

Bottleneck Detection

--------------------------------------------------

GET

/services

Service Relationships

==================================================
AI ENGINE
==================================================

Internal APIs

/api/v1/ai

--------------------------------------------------

POST

/detect

YOLO Detection

--------------------------------------------------

POST

/segment

U-Net Segmentation

--------------------------------------------------

POST

/severity

Severity Prediction

--------------------------------------------------

POST

/gradcam

Generate Heatmap

--------------------------------------------------

POST

/treatment

Treatment Recommendation

--------------------------------------------------

GET

/models

Loaded Models

==================================================
SYSTEM APIs

GET

/health

Every Service

GET

/info

Every Service

GET

/metrics

Every Service

==================================================
HTTP STATUS CODES

200

Success

201

Created

204

Deleted

400

Validation Error

401

Unauthorized

403

Forbidden

404

Not Found

409

Conflict

500

Internal Server Error

==================================================
API SECURITY

JWT Required

Except

Login

Register

Forgot Password

Never expose internal AI APIs.

Gateway only.

==================================================
API DOCUMENTATION

Swagger

OpenAPI 3

Every endpoint

Must contain

Description

Example Request

Example Response

Error Codes

Validation Rules

==================================================

END OF API SPECIFICATION SECTION 1