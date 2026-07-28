# TASK_EXECUTION_PROTOCOL.md

Version: 1.0

Project

AI-Powered Reliable Clinical Decision Support Platform for Kidney Stone Diagnosis Using Explainable AI and Intelligent Microservice Dependency Analysis

------------------------------------------------------------

# PURPOSE

This document defines HOW every engineering task should be executed.

It ensures consistency across the project.

Every implementation must follow this protocol.

Never skip any phase.

------------------------------------------------------------

# ENGINEERING EXECUTION PIPELINE

Every task follows

Requirement

↓

Analysis

↓

Planning

↓

Design

↓

Implementation

↓

Testing

↓

Documentation

↓

Verification

↓

Manifest Update

↓

Completion

Never skip phases.

------------------------------------------------------------

# STEP 1

UNDERSTAND REQUIREMENT

Determine

Feature Request

Bug

Optimization

Refactoring

Research

Documentation

Deployment

Never assume requirements.

------------------------------------------------------------

# STEP 2

READ PROJECT CONTEXT

Always read

PROJECT_MANIFEST.md

AI_RULEBOOK.md

SYSTEM_CONSTITUTION.md

ARCHITECTURE.md

DATABASE.md

API_SPEC.md

SECURITY.md

CODING_STANDARD.md

PROMPT_LIBRARY.md

Never regenerate existing modules.

------------------------------------------------------------

# STEP 3

IMPACT ANALYSIS

Determine

Affected Backend Services

Affected Frontend

Affected Database

Affected APIs

Affected AI Modules

Affected Documentation

Affected Tests

Affected Docker

Return impact summary.

------------------------------------------------------------

# STEP 4

VERIFY ARCHITECTURE

Question

Does the requested feature fit existing architecture?

YES

↓

Continue

NO

↓

Update Architecture.md first

Never implement features outside architecture.

------------------------------------------------------------

# STEP 5

VERIFY DATABASE

Question

Does database change?

If YES

Generate

Migration

ER Update

Database Documentation Update

Manifest Update

If NO

Continue.

------------------------------------------------------------

# STEP 6

VERIFY APIs

Question

New Endpoint?

Existing Endpoint?

Breaking Change?

Always maintain backward compatibility.

Update API_SPEC.md.

------------------------------------------------------------

# STEP 7

PLAN IMPLEMENTATION

Return

Implementation Plan

Affected Files

Affected Modules

Execution Order

Dependencies

Risk Level

Estimated Complexity

------------------------------------------------------------

# STEP 8

IMPLEMENTATION

Follow

Controller

↓

Service

↓

Repository

↓

Database

↓

Frontend

↓

Testing

Never skip layers.

------------------------------------------------------------

# STEP 9

SELF REVIEW

Check

Architecture

Security

Performance

Naming

Code Quality

Documentation

Remove duplication.

------------------------------------------------------------

# STEP 10

TESTING

Generate

Unit Tests

Integration Tests

API Tests

Edge Cases

Negative Cases

Performance Tests

------------------------------------------------------------

# STEP 11

VERIFY SECURITY

JWT

Validation

Authorization

Input Validation

Output Validation

Secrets

Logging

Error Handling

------------------------------------------------------------

# STEP 12

VERIFY PERFORMANCE

Database Queries

Memory Usage

API Calls

Loops

Pagination

Indexes

------------------------------------------------------------

# STEP 13

UPDATE DOCUMENTATION

Update

Architecture.md

Database.md

API_SPEC.md

README.md

PROJECT_MANIFEST.md

CHANGELOG.md

------------------------------------------------------------

# STEP 14

FINAL QUALITY CHECK

Before task completion

Verify

Build Success

Docker Success

Compilation Success

Zero Critical Errors

Zero TODOs

No Duplicate Code

No Dead Code

Documentation Updated

Manifest Updated

Tests Passing

Security Passed

Performance Acceptable

------------------------------------------------------------

# STEP 15

TASK SUMMARY

Return

Task Completed

Files Created

Files Modified

Database Changes

API Changes

Documentation Changes

Risk

Next Recommended Task

------------------------------------------------------------

# BUG FIX PROTOCOL

When fixing bugs

Find Root Cause

Explain Root Cause

Fix Root Cause

Prevent Regression

Generate Tests

Update Documentation

Never patch symptoms.

------------------------------------------------------------

# REFACTOR PROTOCOL

Before Refactoring

Verify

No Architecture Change

No API Break

No Database Break

No Frontend Break

After Refactoring

Run Tests

------------------------------------------------------------

# NEW FEATURE PROTOCOL

Check Existing Code

Reuse Existing Services

Reuse DTOs

Reuse Utilities

Reuse Components

Never duplicate implementation.

------------------------------------------------------------

# AI MODEL PROTOCOL

Training

↓

Evaluation

↓

Export Best Model

↓

Inference Testing

↓

Integration

↓

Documentation

Never deploy untested models.

------------------------------------------------------------

# DATABASE MIGRATION PROTOCOL

Every schema change

Must create

Flyway Migration

Migration Documentation

Rollback Strategy

------------------------------------------------------------

# FRONTEND PROTOCOL

Before creating page

Check

Existing Components

Existing Hooks

Existing APIs

Reuse where possible.

------------------------------------------------------------

# BACKEND PROTOCOL

Before creating service

Check

Existing Services

Existing DTOs

Existing Repository

Reuse where possible.

------------------------------------------------------------

# DOCKER PROTOCOL

Every new service

Must have

Dockerfile

Health Check

Environment Variables

Network Configuration

------------------------------------------------------------

# GIT PROTOCOL

Every completed feature

Commit

Meaningful Message

Update Changelog

Update Manifest

------------------------------------------------------------

# FAILURE RECOVERY

If implementation fails

Rollback

Explain Failure

Identify Cause

Suggest Alternative

Never continue with broken implementation.

------------------------------------------------------------

# AI BEHAVIOR

Think before coding.

Plan before modifying.

Understand before implementing.

Never guess.

Never invent APIs.

Never invent database schema.

Never violate architecture.

------------------------------------------------------------

# DEFINITION OF DONE

Task Complete only if

Architecture Preserved

Database Updated

API Updated

Tests Passing

Docker Working

Documentation Updated

Manifest Updated

Security Passed

Performance Acceptable

Code Reviewed

No Critical Issues

------------------------------------------------------------

END OF DOCUMENT