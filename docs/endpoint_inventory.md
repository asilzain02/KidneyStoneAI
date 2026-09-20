# KidneyStoneAI Definitive Endpoint Inventory

This matrix outlines every functional REST endpoint active within the tested KidneyStoneAI microservice layout accessible via the Gateway (`http://localhost:8080/api/v1`).

| Service | Method | Endpoint | Internal Path | Purpose | Auth | Status |
|---|---|---|---|---|---|---|
| **Auth** | POST | `/api/v1/auth/register` | `/api/v1/auth/register` | Register new user accounts | Public | Active |
| **Auth** | POST | `/api/v1/auth/login` | `/api/v1/auth/login` | Authenticate and issue JWT | Public | Active |
| **Auth** | GET | `/api/v1/auth/profile` | `/api/v1/auth/profile` | Retrieve active user profile payload | Authenticated | Active |
| **Auth** | GET | `/api/v1/auth/users` | `/api/v1/auth/users` | Retrieve all platform users | ADMIN | Active |
| **Patient** | POST | `/api/v1/patients` | `/api/v1/patients` | Create new patient record | ADMIN/DOCTOR | Active |
| **Patient** | GET | `/api/v1/patients` | `/api/v1/patients` | Paginated global list of all patients | Authenticated | Active |
| **Patient** | GET | `/api/v1/patients/{id}`| `/api/v1/patients/{id}` | Retrieve specific patient detail | Authenticated | Active |
| **Image** | POST | `/api/v1/images/upload/{patientId}` | `/api/v1/images/upload/{patientId}` | Accept CT Multipart File upload | ADMIN/DOCTOR | Active |
| **Image** | GET | `/api/v1/images/patient/{patientId}` | `/api/v1/images/patient/{patientId}` | Retrieve all images attached to a patient | Authenticated | Active |
| **Image** | GET | `/api/v1/images/download/{id}` | `/api/v1/images/download/{id}`| Download specific CT Image payload | Authenticated | Active |
| **Diagnosis** | POST | `/api/v1/diagnoses` | `/api/v1/diagnoses` | Execute end-to-end ML inference orchestrator | ADMIN/DOCTOR | Active (Fixed via Gateway) |
| **Diagnosis** | GET | `/api/v1/diagnoses` | `/api/v1/diagnoses` | Paginated global history view | Authenticated | Active (Fixed via Gateway) |
| **Diagnosis** | GET | `/api/v1/diagnoses/{id}`| `/api/v1/diagnoses/{id}` | Retrieve specific diagnosis output values | Authenticated | Active (Fixed via Gateway) |
| **Severity** | POST | `/api/v1/severity/assess` | `/api/v1/severity/assess` | S2S Risk assessment logic | ADMIN/DOCTOR | S2S Only |
| **Treatment** | POST | `/api/v1/treatment/prescribe` | `/api/v1/treatment/prescribe` | S2S Prescriptive bounds | ADMIN/DOCTOR | S2S Only |
| **Report** | GET | `/api/v1/reports` | `/api/v1/reports` | Metadata construction from diagnosis service | ADMIN/DOCTOR | Active |
| **Report** | POST | `/api/v1/reports/generate` | `/api/v1/reports/generate` | Compile AI and Patient data into PDF structure | ADMIN/DOCTOR | Active |

---

# KidneyStoneAI Frontend to Microservice Mapping Matrix

| React Route | Primary Features | React Query Hook Node | Target `apiClient` Endpoint | Microservice Handler |
|---|---|---|---|---|
| `/login` | User Authentication | `useAuth().login()` | `POST /api/v1/auth/login` | `Auth Service` |
| `/dashboard` | System Statistics Base | N/A (Aggregates Cache) | N/A | N/A |
| `/patients` | Global Patient Paginated Listing | `patientApi.getPatients` | `GET /api/v1/patients` | `Patient Service` |
| `/patients` -> (Add) | Open Add Patient Modal | `patientApi.createPatient` | `POST /api/v1/patients` | `Patient Service` |
| `/patients/:id` | Unified Context Profile View | `patientApi.getPatient` | `GET /api/v1/patients/{id}` | `Patient Service` |
| `/images` | Patient Selector / Upload View | `patientApi.getPatients` | `GET /api/v1/patients` | `Patient Service` |
| `/images` -> (Upload) | Attach Multipart Image to UID | `imageApi.uploadImage` | `POST /api/v1/images/upload/{id}` | `Image Service` (Now saves custom `fileName` to MedicalImage DB seamlessly!) |
| `/*/images/:id` | Inline Preview Blob Resolver | N/A (Browser Auth Direct) | `GET /api/v1/images/download/{id}` | `Image Service` |
| `/diagnoses` | Global Diagnosis History Listing | `diagnosisApi.getDiagnoses` | `GET /api/v1/diagnoses` | `Diagnosis Service` |
| `/diagnoses` -> (Run) | Start AI Process Orchestration | `diagnosisApi.createDiagnosis` | `POST /api/v1/diagnoses` | `Diagnosis Service` |
| `/diagnoses/:id` | Read-Only Result Inspection | `diagnosisApi.getDiagnosis` | `GET /api/v1/diagnoses/{id}` | `Diagnosis Service` (Returns aggregated Severity + Treatment inside payload) |
| `/reports` | Discovered Verified Report Log | `reportApi.getReports` | `GET /api/v1/reports` | `Report Service` |
| `/reports` (Click) | Download Proxy Blob Invocation| `reportApi.downloadReport` | `GET /api/v1/diagnoses/{id}/report` | `Diagnosis -> Report` |
| `/settings` | Current Session & Preferences | `authApi.getProfile` | `GET /api/v1/auth/profile` | `Auth Service` |
| `/users` | Secure Admin User Listing Viewer | `authApi.getUsers` | `GET /api/v1/auth/users` | `Auth Service` |
| Default `ErrorBoundary` | Graceful Crash & Routing UI | N/A (React Error Catch) | N/A | Client Rendering |
