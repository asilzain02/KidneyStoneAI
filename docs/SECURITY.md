# SECURITY.md

Version: 1.0

Project

AI-Powered Reliable Clinical Decision Support Platform for Kidney Stone Diagnosis Using Explainable AI and Intelligent Microservice Dependency Analysis

---

# PURPOSE

This document defines the complete security architecture of the platform.

Every service must follow these rules.

Security is mandatory.

Never bypass security.

------------------------------------------------------------

# SECURITY PRINCIPLES

Zero Trust

Least Privilege

Defense in Depth

Secure by Default

Fail Secure

Input Validation

Output Encoding

Authentication First

Authorization Second

Never Trust Client Input

------------------------------------------------------------

# AUTHENTICATION

Method

JWT

Algorithm

HS256

Access Token

15 Minutes

Refresh Token

7 Days

Every request except

/login

/register

/forgot-password

Requires JWT.

------------------------------------------------------------

# AUTHORIZATION

Role Based Access Control

Roles

ADMIN

DOCTOR

PATIENT

Permissions

ADMIN

Full Access

DOCTOR

Patient

Diagnosis

Reports

PATIENT

Own Reports

Own Profile

Never use role names directly inside controllers.

Use Spring Security Authorities.

------------------------------------------------------------

# PASSWORD POLICY

Minimum Length

8

Recommended

12+

Must contain

Uppercase

Lowercase

Number

Special Character

Never store passwords.

Store BCrypt Hash only.

BCrypt Strength

12

------------------------------------------------------------

# JWT RULES

Never store JWT in Local Storage.

Use Secure HTTP Only Cookies when production.

Development

Authorization Header

Bearer Token

Never expose JWT Secret.

JWT Secret

Environment Variable Only

------------------------------------------------------------

# SESSION MANAGEMENT

Stateless Authentication

No Server Session

Logout

Invalidate Refresh Token

------------------------------------------------------------

# API SECURITY

Every Request

Validated

Sanitized

Authenticated

Authorized

Rate Limited

Every API

Uses HTTPS

Never expose Internal APIs.

Gateway Only.

------------------------------------------------------------

# INPUT VALIDATION

Validate

Email

Phone

UUID

Age

Height

Weight

BMI

Image Size

Image Type

Maximum Upload

100 MB

Allowed Formats

DICOM

PNG

JPEG

JPG

Reject Everything Else.

------------------------------------------------------------

# FILE UPLOAD SECURITY

Allowed MIME Types Only

Virus Scan Ready

Random File Names

No Original Names

Store Outside Public Directory

Validate Extension

Validate MIME Type

Validate Size

Generate SHA256 Checksum

------------------------------------------------------------

# SQL SECURITY

Use Spring Data JPA

Parameterized Queries

Prepared Statements

Never Build SQL Using String Concatenation

Prevent

SQL Injection

------------------------------------------------------------

# XSS PROTECTION

Escape Output

React Auto Escape

Never Render Raw HTML

Never Use

dangerouslySetInnerHTML

------------------------------------------------------------

# CSRF

Development

Disabled

Production

Enabled

------------------------------------------------------------

# CORS

Allow

Frontend URL Only

Never Allow

*

Origins

Development

localhost

Production

Configured Domain

------------------------------------------------------------

# RATE LIMITING

Login

5 Requests

Per Minute

Prediction API

20 Requests

Per Minute

Upload API

10 Requests

Per Minute

------------------------------------------------------------

# DATA ENCRYPTION

Passwords

BCrypt

Sensitive Data

AES-256 Ready

Database Connection

SSL

API

HTTPS

------------------------------------------------------------

# ENVIRONMENT VARIABLES

Never Hardcode

Database Password

JWT Secret

API Keys

Email Password

Model Paths

Always Read From

.env

application.yml

------------------------------------------------------------

# LOGGING SECURITY

Never Log

Passwords

JWT

Refresh Tokens

Medical Images

Patient Passwords

Sensitive Data

Allowed

User ID

Request ID

Timestamp

Endpoint

Execution Time

------------------------------------------------------------

# AUDIT LOGGING

Every Critical Action

Login

Logout

Prediction

Patient Update

Image Upload

Report Download

Admin Action

Must Be Logged

------------------------------------------------------------

# DATABASE SECURITY

Least Privilege

Separate DB User

Read Only User

Reporting User

Application User

Never Use PostgreSQL Superuser

------------------------------------------------------------

# MEDICAL DATA SECURITY

Patient Data

Private

Never Expose

Clinical History

Without Authorization

Medical Images

Private

Reports

Private

Follow

HIPAA Inspired Design

(Not Official Compliance)

------------------------------------------------------------

# ERROR HANDLING

Never Return

Stack Trace

Database Errors

SQL Errors

Internal Class Names

Return

Friendly Messages

------------------------------------------------------------

# DOCKER SECURITY

Run Containers

Non Root User

Limit Memory

Limit CPU

Read Only Volumes

Secrets Through Environment Variables

------------------------------------------------------------

# DEPENDENCY SECURITY

Use Latest Stable Libraries

No Deprecated Libraries

Check CVEs Before Upgrading

------------------------------------------------------------

# SPRING SECURITY

Use

Spring Security

JWT Filter

BCrypt

Authentication Manager

Method Security

Global Exception Handler

------------------------------------------------------------

# PYTHON SECURITY

Validate Inputs

Limit File Size

Never Execute Uploaded Files

Never Use eval()

Never Trust Pickle Files

Use Virtual Environment

------------------------------------------------------------

# FRONTEND SECURITY

Sanitize Forms

Validate Inputs

No Secrets In Frontend

No Hardcoded API Keys

Store Configuration Separately

------------------------------------------------------------

# OWASP TOP 10

The project should protect against

SQL Injection

Broken Authentication

Sensitive Data Exposure

Broken Access Control

Security Misconfiguration

XSS

Insecure Deserialization

Using Vulnerable Components

Insufficient Logging

SSRF

------------------------------------------------------------

# SECURITY CHECKLIST

Before Every Release

✔ JWT Working

✔ BCrypt Enabled

✔ Input Validation

✔ HTTPS Ready

✔ SQL Injection Safe

✔ XSS Safe

✔ Role Based Access

✔ Logs Reviewed

✔ Secrets Hidden

✔ Docker Secure

✔ Error Messages Safe

✔ Audit Logs Enabled

------------------------------------------------------------

# RULES FOR AI

Never generate insecure code.

Never hardcode secrets.

Never bypass authentication.

Never expose internal APIs.

Always validate input.

Always use DTOs.

Always hash passwords.

Always sanitize uploaded files.

Always follow this document.

END OF SECURITY DOCUMENT