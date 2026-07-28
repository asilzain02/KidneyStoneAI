# DATABASE.md

Version: 1.0

Project

AI-Powered Reliable Clinical Decision Support Platform for Kidney Stone Diagnosis Using Explainable AI and Intelligent Microservice Dependency Analysis

---

# DATABASE DESIGN

## OBJECTIVE

The database must satisfy the following requirements:

• Modular

• Secure

• Highly Normalized

• Easily Scalable

• Healthcare Ready

• Microservice Friendly

• Audit Enabled

• Soft Delete Enabled

• Future Cloud Ready

The database must support all microservices while maintaining clear ownership of data.

---

# DATABASE ENGINE

Database

PostgreSQL 16

Character Set

UTF-8

Timezone

UTC

Connection Pool

HikariCP

ORM

Spring Data JPA

Migration Tool

Flyway

---

# DATABASE STRATEGY

Database Type

Relational

Architecture

Single PostgreSQL Instance

Multiple Schemas

Future Upgrade

Database Per Service

Current Design

Authentication Schema

Patient Schema

Diagnosis Schema

Monitoring Schema

---

# DATABASE RULES

Every table MUST have

id

created_at

updated_at

created_by

updated_by

is_deleted

version

Every Primary Key

UUID

Never use AUTO_INCREMENT.

Always use UUID.

---

# NAMING CONVENTIONS

Tables

snake_case

Example

patient

stone_prediction

clinical_history

Columns

snake_case

Example

patient_id

stone_size

prediction_confidence

Constraints

pk_patient

fk_patient_history

idx_patient_name

---

# AUDIT COLUMNS

Every table

id UUID

created_at TIMESTAMP

updated_at TIMESTAMP

created_by UUID

updated_by UUID

is_deleted BOOLEAN

version INTEGER

Purpose

Audit

Optimistic Locking

Soft Delete

History

---

# DATABASE SCHEMAS

authentication

patient

diagnosis

monitoring

Future

analytics

notification

billing

---

==========================================================

AUTHENTICATION SCHEMA

==========================================================

Table

users

Purpose

Application Users

Columns

id

username

email

password_hash

role_id

first_name

last_name

phone

status

last_login

created_at

updated_at

created_by

updated_by

is_deleted

version

Indexes

email

username

Foreign Keys

role_id

----------------------------------------------------------

Table

roles

Purpose

Role Management

Columns

id

role_name

description

created_at

updated_at

created_by

updated_by

is_deleted

version

----------------------------------------------------------

Table

permissions

Purpose

Permission List

Columns

id

permission_name

description

----------------------------------------------------------

Table

role_permission

Purpose

Many to Many Mapping

Columns

role_id

permission_id

----------------------------------------------------------

Table

refresh_token

Purpose

JWT Refresh Tokens

Columns

id

user_id

token

expiry_date

revoked

==========================================================

PATIENT SCHEMA

==========================================================

Table

patient

Purpose

Stores Patient Information

Columns

id

patient_code

first_name

last_name

gender

date_of_birth

blood_group

phone

email

address

city

state

country

height

weight

bmi

emergency_contact

status

created_at

updated_at

created_by

updated_by

is_deleted

version

Indexes

patient_code

phone

email

----------------------------------------------------------

Table

clinical_history

Purpose

Patient Medical History

Columns

id

patient_id

diabetes

hypertension

kidney_disease

family_history

previous_stone

allergy

smoking

alcohol

remarks

created_at

updated_at

Foreign Key

patient_id

----------------------------------------------------------

Table

visit_history

Purpose

Hospital Visits

Columns

id

patient_id

visit_date

doctor_name

diagnosis

prescription

notes

==========================================================

IMAGE SCHEMA

==========================================================

Table

image_metadata

Purpose

CT Scan Metadata

Columns

id

patient_id

file_name

file_path

image_type

image_size

width

height

format

checksum

uploaded_by

upload_time

Foreign Keys

patient_id

Indexes

patient_id

==========================================================

DIAGNOSIS SCHEMA

==========================================================

Table

stone_prediction

Purpose

Stores AI Predictions

Columns

id

patient_id

image_id

prediction_label

confidence

processing_time

model_version

prediction_date

Foreign Keys

patient_id

image_id

----------------------------------------------------------

Table

stone_detection

Purpose

Bounding Box Information

Columns

id

prediction_id

stone_count

x_coordinate

y_coordinate

width

height

confidence

----------------------------------------------------------

Table

stone_segmentation

Purpose

Segmentation Result

Columns

id

prediction_id

mask_path

area

perimeter

volume

shape

----------------------------------------------------------

Table

stone_measurement

Purpose

Stone Measurements

Columns

id

prediction_id

stone_length

stone_width

stone_height

stone_density

stone_location

==========================================================

SEVERITY SCHEMA

==========================================================

Table

severity_assessment

Columns

id

prediction_id

severity_level

risk_score

explanation

assessment_date

==========================================================

TREATMENT SCHEMA

==========================================================

Table

treatment_recommendation

Columns

id

severity_id

recommended_treatment

medication

hydration

follow_up_days

doctor_notes

==========================================================

REPORT SCHEMA

==========================================================

Table

diagnostic_report

Columns

id

patient_id

prediction_id

severity_id

report_path

generated_at

generated_by

==========================================================

MONITORING SCHEMA

==========================================================

Table

service_metrics

Columns

id

service_name

cpu_usage

memory_usage

disk_usage

latency

response_time

request_count

error_count

collection_time

----------------------------------------------------------

Table

service_health

Columns

id

service_name

health_status

status_message

last_checked

==========================================================

DEPENDENCY ANALYZER SCHEMA

==========================================================

Table

dependency_graph

Columns

id

source_service

destination_service

relationship_type

call_frequency

dependency_weight

----------------------------------------------------------

Table

failure_prediction

Columns

id

service_name

failure_probability

predicted_failure_time

risk_level

recommendation

prediction_time

----------------------------------------------------------

Table

root_cause_analysis

Columns

id

failure_prediction_id

root_service

affected_services

analysis

confidence

==========================================================

DATABASE RELATIONSHIPS

users

↓

roles

patient

↓

clinical_history

↓

visit_history

↓

image_metadata

↓

stone_prediction

↓

stone_detection

↓

stone_segmentation

↓

stone_measurement

↓

severity_assessment

↓

treatment_recommendation

↓

diagnostic_report

----------------------------------------------------------

MONITORING

service_metrics

↓

service_health

↓

dependency_graph

↓

failure_prediction

↓

root_cause_analysis

==========================================================

DATABASE DESIGN PRINCIPLES

✓ Third Normal Form

✓ UUID Primary Keys

✓ Foreign Keys

✓ Soft Delete

✓ Audit Columns

✓ Versioning

✓ Optimistic Locking

✓ Indexed Search Fields

✓ Future Cloud Migration Support

✓ Multi Schema Ready

                END OF DATABASE SECTION 1

============================================================
DATABASE SECTION 2
TABLE DEFINITIONS
============================================================

DATABASE STANDARD

Every table MUST follow these standards.

Primary Key

UUID

NOT NULL

DEFAULT gen_random_uuid()

Every table contains

id

created_at

updated_at

created_by

updated_by

is_deleted

version

------------------------------------------------------------

PATIENT TABLE

Table Name

patient

Purpose

Stores patient master information.

Columns

id UUID PRIMARY KEY

patient_code VARCHAR(30) UNIQUE NOT NULL

first_name VARCHAR(100)

last_name VARCHAR(100)

gender VARCHAR(20)

date_of_birth DATE

blood_group VARCHAR(5)

phone VARCHAR(20)

email VARCHAR(150)

address TEXT

city VARCHAR(100)

state VARCHAR(100)

country VARCHAR(100)

height DECIMAL(5,2)

weight DECIMAL(5,2)

bmi DECIMAL(5,2)

emergency_contact VARCHAR(20)

status VARCHAR(30)

created_at TIMESTAMP

updated_at TIMESTAMP

created_by UUID

updated_by UUID

is_deleted BOOLEAN DEFAULT FALSE

version INTEGER DEFAULT 1

Indexes

patient_code

phone

email

Constraints

Patient code unique

Email unique

Phone unique

------------------------------------------------------------

CLINICAL_HISTORY

Primary Key

id

Foreign Key

patient_id

Columns

patient_id UUID

diabetes BOOLEAN

hypertension BOOLEAN

kidney_disease BOOLEAN

family_history BOOLEAN

previous_stone BOOLEAN

smoking BOOLEAN

alcohol BOOLEAN

allergy TEXT

notes TEXT

Relationship

One Patient

↓

Many Clinical Records

------------------------------------------------------------

VISIT_HISTORY

Primary Key

id

Foreign Key

patient_id

Columns

visit_date TIMESTAMP

doctor_name VARCHAR(100)

complaints TEXT

diagnosis TEXT

prescription TEXT

remarks TEXT

Relationship

Patient

↓

Many Visits

------------------------------------------------------------

IMAGE_METADATA

Purpose

Store uploaded CT image information.

Columns

id UUID

patient_id UUID

file_name VARCHAR(255)

file_path TEXT

image_type VARCHAR(50)

file_size BIGINT

width INTEGER

height INTEGER

checksum VARCHAR(255)

upload_time TIMESTAMP

uploaded_by UUID

Indexes

patient_id

checksum

Never duplicate images.

------------------------------------------------------------

STONE_PREDICTION

Purpose

Prediction Result

Columns

id UUID

patient_id UUID

image_id UUID

prediction_label VARCHAR(50)

confidence DECIMAL(5,2)

processing_time DECIMAL(10,2)

model_name VARCHAR(50)

model_version VARCHAR(20)

prediction_time TIMESTAMP

Indexes

patient_id

prediction_time

------------------------------------------------------------

STONE_DETECTION

Purpose

Bounding Boxes

Columns

id UUID

prediction_id UUID

stone_number INTEGER

x_coordinate DECIMAL

y_coordinate DECIMAL

width DECIMAL

height DECIMAL

confidence DECIMAL

Relationship

One Prediction

↓

Many Stones

------------------------------------------------------------

STONE_SEGMENTATION

Purpose

Segmentation Information

Columns

id UUID

prediction_id UUID

mask_path TEXT

mask_area DECIMAL

perimeter DECIMAL

volume DECIMAL

shape VARCHAR(100)

Indexes

prediction_id

------------------------------------------------------------

STONE_MEASUREMENT

Purpose

Medical Measurements

Columns

id UUID

prediction_id UUID

stone_length DECIMAL

stone_width DECIMAL

stone_height DECIMAL

stone_density DECIMAL

stone_volume DECIMAL

stone_location VARCHAR(100)

measurement_unit VARCHAR(20)

------------------------------------------------------------

SEVERITY_ASSESSMENT

Purpose

Severity Prediction

Columns

id UUID

prediction_id UUID

severity_level VARCHAR(30)

risk_score DECIMAL(5,2)

recommendation_level VARCHAR(100)

explanation TEXT

assessment_time TIMESTAMP

------------------------------------------------------------

TREATMENT_RECOMMENDATION

Columns

id UUID

severity_id UUID

recommended_treatment TEXT

medication TEXT

hydration TEXT

follow_up_days INTEGER

doctor_notes TEXT

------------------------------------------------------------

DIAGNOSTIC_REPORT

Columns

id UUID

patient_id UUID

prediction_id UUID

severity_id UUID

report_path TEXT

generated_at TIMESTAMP

generated_by UUID

status VARCHAR(30)

------------------------------------------------------------

SERVICE_METRICS

Purpose

Monitor Runtime

Columns

id UUID

service_name VARCHAR(100)

cpu_usage DECIMAL

memory_usage DECIMAL

disk_usage DECIMAL

response_time DECIMAL

latency DECIMAL

request_count BIGINT

error_count BIGINT

collection_time TIMESTAMP

Indexes

service_name

collection_time

------------------------------------------------------------

SERVICE_HEALTH

Columns

id UUID

service_name VARCHAR(100)

status VARCHAR(30)

message TEXT

last_checked TIMESTAMP

------------------------------------------------------------

DEPENDENCY_GRAPH

Columns

id UUID

source_service VARCHAR(100)

destination_service VARCHAR(100)

relationship_type VARCHAR(50)

call_frequency BIGINT

dependency_weight DECIMAL

last_updated TIMESTAMP

------------------------------------------------------------

FAILURE_PREDICTION

Columns

id UUID

service_name VARCHAR(100)

failure_probability DECIMAL

risk_level VARCHAR(30)

prediction_time TIMESTAMP

recommendation TEXT

------------------------------------------------------------

ROOT_CAUSE_ANALYSIS

Columns

id UUID

failure_prediction_id UUID

root_service VARCHAR(100)

affected_services TEXT

analysis TEXT

confidence DECIMAL

------------------------------------------------------------

UNIQUE CONSTRAINTS

Patient Code

Email

Phone

Checksum

Prediction ID

------------------------------------------------------------

CHECK CONSTRAINTS

Confidence

0–100

CPU Usage

0–100

Memory Usage

0–100

Disk Usage

0–100

BMI

Greater than Zero

Risk Score

0–100

------------------------------------------------------------

CASCADE RULES

Patient

↓

Clinical History

ON DELETE RESTRICT

Patient

↓

Image

ON DELETE RESTRICT

Prediction

↓

Detection

ON DELETE CASCADE

Prediction

↓

Segmentation

ON DELETE CASCADE

Prediction

↓

Measurement

ON DELETE CASCADE

Severity

↓

Treatment

ON DELETE CASCADE

------------------------------------------------------------

INDEX STRATEGY

Create indexes for

Patient Code

Email

Phone

Prediction Date

Service Name

Collection Time

Severity Level

Failure Probability

Never over-index.

------------------------------------------------------------

DATABASE OPTIMIZATION

Use UUID

Use Foreign Keys

Normalize Tables

Avoid Duplicate Data

Use Lazy Loading

Use Batch Inserts

Use Pagination

Avoid SELECT *

Avoid N+1 Queries

Use Connection Pooling

------------------------------------------------------------

BACKUP STRATEGY

Daily Full Backup

Hourly Incremental Backup

Transaction Logs

Retention

30 Days

------------------------------------------------------------

SECURITY

Passwords

Never stored.

Only BCrypt Hash.

Patient Data

Encrypted.

JWT Secret

Environment Variable.

Database Password

Environment Variable.

------------------------------------------------------------

                END OF DATABASE SECTION 2        