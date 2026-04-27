# Final Studies Project – Second Part: Leveraging Meteorological Data for Agricultural Risk Prevention

This repository contains the **second part of the Final Studies Project**, which focuses on developing a **demonstration dashboard for agricultural risk prevention**. The project integrates **weather forecasting machine learning models** with a user-friendly interface, showcasing how predictive analytics can support farming decisions.

The dashboard development was structured using the **PDCA (Plan–Do–Check–Act)** Lean continuous improvement cycle, with **5S principles** applied to system organization and the **Control phase of DMAIC** to sustain the forecasting improvements delivered in Part 1.

---

## Table of Contents

1. [Dashboard Overview](#dashboard-overview)
2. [Methodology & Quality Framework](#methodology--quality-framework)
3. [Dashboard Structure](#dashboard-structure)
4. [System Architecture](#system-architecture)
5. [Features](#features)
6. [Implementation Results](#implementation-results)
7. [Limitations](#limitations)
8. [Technologies Used](#technologies-used)

---

## Dashboard Overview

The dashboard acts as a **proof-of-concept** to demonstrate how weather prediction models can be used in real-life agriculture. It provides interactive features for both **clients (farmers)** and **admins**, including weather forecasts, personalized recommendations, educational content, and system management tools.

This project also serves as a **prototype for future integration** with the company's main platform, **WeeFarm** — and represents the **Control phase** of the DMAIC Six Sigma framework applied across the full Final Studies Project.

---

## Methodology & Quality Framework

This part of the project was developed using the **PDCA (Plan–Do–Check–Act)** Lean continuous improvement cycle, ensuring structured delivery, quality assurance, and sustained value at every development phase.

### Plan
- Defined the dashboard's dual-user scope (farmers and admins) and mapped functional requirements to model outputs from Part 1.
- Designed a **3-tier architecture** (Presentation → Application → Data) to ensure separation of concerns, maintainability, and scalability readiness.
- Established quality objectives: real-time ML integration, secure authentication, responsive UI, and admin-level monitoring.
- Applied **5S principles** to structure the project repository and codebase:
  - **Sort:** Separated frontend, backend, and ML API into independent, well-scoped modules.
  - **Set in Order:** Standardized folder structure and API contracts across all three tiers.
  - **Shine:** Maintained clean, documented code and consistent naming conventions.
  - **Standardize:** Unified authentication flows, API response formats, and error handling patterns.
  - **Sustain:** Implemented logging and activity monitoring to ensure long-term system observability.

### Do
- Built the **React/Vite.js frontend** — responsive client and admin dashboards with weather forecasts, personalized farming recommendations, educational articles, and support ticket management.
- Developed the **Node.js/Express.js backend** — handling API requests, authentication (login, registration, password recovery), and business logic for both user roles.
- Deployed the **Flask ML API** — serving trained LSTM weather forecasting models, generating real-time 3-day predictions and farming recommendations, and storing results in MongoDB Atlas.
- Integrated all three tiers end-to-end, validated with Postman API testing.

### Check
- Conducted structured **root cause analysis** on integration gaps between the ML API and backend to ensure prediction outputs were correctly consumed and displayed.
- Evaluated system behavior across all key user flows: authentication, forecast display, article interaction, admin analytics, and support ticket handling.
- Identified current limitations through a systematic gap analysis:
  - Local deployment only (not yet cloud-ready)
  - Not designed for high-volume concurrent users
  - Basic security — advanced features not yet implemented

### Act
- Documented all limitations and scoped a **future improvement roadmap**: cloud deployment, scalability for high-volume requests, advanced security features, and A/B testing of recommendation strategies.
- Standardized the dashboard as a reproducible prototype for future integration into the **WeeFarm** platform, sustaining the forecasting improvements from Part 1's DMAIC Control phase.

---

## Dashboard Structure

| Module | Description |
|--------|-------------|
| `farmer-dashboard` | React + Vite.js frontend — responsive, interactive UI for clients and admins |
| `farmer-dashboard-back` | Node.js + Express.js backend — API requests, authentication, business logic |
| `ml-api` | Flask ML API — serves LSTM forecasting models, generates recommendations |
| `package.json` | Node.js project metadata and dependencies |

---

## System Architecture

The dashboard follows a **3-tier architecture**, scoped and standardized using **5S principles** for clean separation of concerns:

```
┌─────────────────────────────────────┐
│        Presentation Layer           │
│   React + Vite.js + TailwindCSS     │
│  Forecasts · Recommendations · UI   │
└────────────────┬────────────────────┘
                 │ API Requests
┌────────────────▼────────────────────┐
│         Application Layer           │
│       Node.js + Express.js          │
│  Auth · Business Logic · Routing    │
└──────────┬──────────────┬───────────┘
           │              │
┌──────────▼──────┐  ┌────▼────────────┐
│   Data Layer    │  │    ML API Layer  │
│  MongoDB Atlas  │  │  Flask + LSTM    │
│ Users · Logs ·  │  │ 3-day Forecasts  │
│ Forecasts       │  │ Recommendations  │
└─────────────────┘  └─────────────────┘
```

### Key Components

| Component | Role |
|-----------|------|
| **Authentication** | Secure login, registration, and password recovery for clients and admins |
| **Client Dashboard** | Weather forecasts, personalized farming advice, educational articles, support tickets |
| **Admin Dashboard** | User management, analytics, logs, support request handling |
| **ML API Integration** | Real-time 3-day predictions via trained LSTM models from Part 1 |

---

## Features

- 🌦️ Interactive weather forecast module with **3-day predictions**
- 🌱 Personalized farming recommendations based on LSTM model outputs
- 📰 Educational articles with client interaction (comments, reviews)
- 📊 Admin analytics dashboard for monitoring system usage and engagement
- 🔐 User management and role-based access control
- 🎫 Support ticket system for client assistance
- 📋 Logging and activity monitoring for administrators

---

## Implementation Results

| Page | Description |
|------|-------------|
| **Login Page** | Secure authentication for all users |
| **Client Pages** | Weather predictions, farming recommendations, educational articles |
| **Admin Pages** | Analytics dashboard, user management, logs, support handling |
| **ML API** | LSTM forecasting models integrated seamlessly for real-time recommendations |

Screenshots of key pages are included in the documentation folder for reference.

---

## Limitations

Identified through systematic **gap analysis** (Check phase of PDCA):

| Limitation | Description |
|------------|-------------|
| **Local Deployment** | Not yet cloud-ready; cannot handle multiple simultaneous users |
| **Scalability** | Not designed for high-volume weather requests or large user databases |
| **Security** | Basic login and permission system; advanced features not yet implemented |
| **Proof-of-Concept** | Focus on demonstration and integration, not commercial-ready product |

---

## Technologies Used

| Category | Tools |
|----------|-------|
| Front-end | React, Vite.js, TailwindCSS |
| Back-end | Node.js, Express.js |
| ML API | Python, Flask, LSTM models |
| Database | MongoDB Atlas |
| Dev Tools | Git, VSCode, Postman |
| Quality Framework | PDCA (Lean), 5S, DMAIC Control Phase, Root Cause Analysis |

---

## Future Work

Defined as part of the **Act phase** of the PDCA cycle:

- ☁️ Cloud deployment for scalability and multi-user support
- 🔒 Advanced security features (JWT refresh tokens, rate limiting, HTTPS)
- 📈 A/B testing of farming recommendation strategies
- 🔁 Full integration into the **WeeFarm** production platform
- 🤖 Deep learning extensions (attention-based regression, real-time data streaming)
