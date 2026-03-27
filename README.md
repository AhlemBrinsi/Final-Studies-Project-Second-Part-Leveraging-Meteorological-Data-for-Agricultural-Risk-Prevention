# Final Studies Project - Second Part: Leveraging Meteorological Data for Agricultural Risk Prevention

This repository contains the **second part of the Final Studies Project**, which focuses on developing a **demonstration dashboard for agricultural risk prevention**. The project integrates **weather forecasting machine learning models** with a user-friendly interface, showcasing how predictive analytics can support farming decisions.

## Table of Contents

1. [Project Overview](#project-overview)  
2. [Project Structure](#project-structure)  
3. [System Architecture](#system-architecture)  
   - [Key Components](#key-components)  
4. [Features](#features)  
5. [Implementation Results](#implementation-results)  
6. [Limitations](#limitations)  
7. [Technologies Used](#technologies-used)

---

## Project Overview

The dashboard acts as a **proof-of-concept** to demonstrate how weather prediction models can be used in real-life agriculture. It provides interactive features for both **clients (farmers)** and **admins**, including weather forecasts, personalized recommendations, educational content, and system management tools. 

This project also serves as a **prototype for future integration** with the company’s main platform, **WeeFarm**.

---

## Project Structure

- **farmer-dashboard**: Front-end application built with **React** and **Vite.js** for a responsive and interactive user experience.
- **farmer-dashboard-back**: Back-end server using **Node.js** and **Express.js**, handling API requests, authentication, and business logic.
- **ml-api**: Machine Learning API built with **Flask**, serving weather forecasting models and generating recommendations.
- **.vscode**: VSCode workspace settings (optional).
- **node_modules**: Node.js dependencies (auto-generated).
- `package.json` & `package-lock.json`: Node.js project metadata and dependencies.

---

## System Architecture

The dashboard is designed with a **three-tier architecture**:

1. **Presentation Layer**: React frontend displays forecasts, recommendations, articles, and user interactions.
2. **Application Layer**: Node.js backend handles API requests, authentication, and business logic.
3. **Data Layer**: MongoDB Atlas stores user profiles, forecasts, articles, and logs. The Flask ML API processes weather predictions and stores results in the database.

**Key Components:**

- **Authentication**: Supports secure login, registration, and password recovery for **clients** and **admins**.
- **Client Dashboard**: Displays weather forecasts, personalized farming advice, educational articles, and support tickets.
- **Admin Dashboard**: Manages users, articles, analytics, logs, and support requests.
- **ML API Integration**: Provides real-time predictions using trained LSTM weather forecasting models.

---

## Features

- Interactive weather forecast module with **3-day predictions**.
- Personalized farming recommendations based on model outputs.
- Educational articles and client interaction (comments, reviews).
- Admin analytics for monitoring system usage and engagement.
- User management and access control for secure operations.
- Support ticket system for client assistance.
- Logging and activity monitoring for administrators.

---

## Implementation Results

- **Login Page**: Secure authentication for all users.
- **Client Pages**: Weather predictions, recommendations, and articles.
- **Admin Pages**: Analytics dashboard, user management, logs, and support handling.
- **ML API**: Predictive models integrated seamlessly for real-time recommendations.

**Screenshots** of key pages are included in the documentation folder for reference.

---

## Limitations

- **Local Deployment Only**: The system is not yet cloud-ready and cannot handle multiple simultaneous users.
- **Scalability**: Not designed for high-volume weather requests or large user databases.
- **Security**: Basic login and permission system; advanced security features are not implemented.
- **Proof-of-Concept**: The focus is on demonstration and integration rather than a fully commercial-ready product.

---

## Technologies Used

- **Front-end**: React, Vite.js, TailwindCSS
- **Back-end**: Node.js, Express.js
- **Machine Learning API**: Python, Flask, LSTM models
- **Database**: MongoDB Atlas
- **Tools**: Git, VSCode, Postman (for API testing)

---
