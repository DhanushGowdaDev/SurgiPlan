# SurgiPlan

### Intelligent Operating Room Scheduling & Resource Optimization

**Optimize every operating room. Adapt to every change.**

SurgiPlan is an operating room scheduling and resource optimization platform that combines constraint programming with AI-assisted interaction to help coordinate surgical procedures, operating rooms, medical staff, equipment, and recovery beds.

Built with **Google OR-Tools CP-SAT**, **FastAPI**, and **Google Gemma**, SurgiPlan separates scheduling decisions from natural-language assistance to support constraint-aware optimization and explainable operational workflows.

> **Design principle:** OR-Tools determines the schedule. Gemma assists with natural-language interaction and explanations without replacing the optimization engine.

---

## Table of Contents

- [Overview](#overview)
- [Key Capabilities](#key-capabilities)
- [How It Works](#how-it-works)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Deployment](#deployment)
- [Security](#security)
- [Roadmap](#roadmap)
- [Disclaimer](#disclaimer)
- [Author](#author)

---

## Overview

Operating room scheduling requires coordinating multiple resources while satisfying operational constraints. Surgery durations, room suitability, staff availability, equipment capacity, and recovery-bed requirements can all affect scheduling feasibility.

SurgiPlan models these requirements as a constraint optimization problem and uses OR-Tools CP-SAT to search for feasible schedules. Its AI Copilot provides a natural-language interface for interacting with scheduling information and understanding optimization outcomes.

### Key Capabilities

| Capability | Description |
|---|---|
| **Intelligent Scheduling** | Optimize operating room assignments and surgery start times using OR-Tools CP-SAT. |
| **Emergency Scheduling** | Evaluate emergency scheduling requests against operational constraints. |
| **Resource Management** | Coordinate surgical cases, operating rooms, staff, equipment, and recovery resources. |
| **Constraint Validation** | Account for procedure duration, staff availability, equipment capacity, and room suitability. |
| **Scenario Simulation** | Explore alternative scheduling scenarios and evaluate their potential impact. |
| **AI Copilot** | Interact with scheduling information using natural language. |
| **Optimization History** | Review recorded optimization results when available. |
| **Web Dashboard** | View and interact with scheduling information through a React-based interface. |

---

## How It Works

SurgiPlan follows a workflow that separates optimization, validation, and AI-assisted explanation.

1. **Input** — Load surgical cases, operating rooms, staff, equipment, and recovery requirements.
2. **Model** — Represent operational requirements as constraints.
3. **Optimize** — Use OR-Tools CP-SAT to search for a feasible, optimized schedule.
4. **Validate** — Evaluate scheduling feasibility and resource conflicts.
5. **Explain** — Use the AI Copilot to interpret natural-language requests and help explain scheduling outcomes.

The optimization solver remains the authority for schedule generation. AI-assisted explanations do not replace solver results or operational validation.

---

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Styling | Tailwind CSS |
| Backend API | Python, FastAPI |
| Optimization | Google OR-Tools CP-SAT |
| AI Assistance | Google Gemma, Google Gen AI SDK |
| Database | MongoDB Atlas |
| Data Visualization | Recharts |
| Frontend Deployment | Vercel |
| Backend Deployment | Render |
| Version Control | Git, GitHub |

---

## Architecture

SurgiPlan uses a modular architecture in which the frontend communicates with backend services through a REST API. The backend coordinates scheduling optimization, resource validation, database access, and AI integration.

```text
┌─────────────────────────────────────┐
│       React + TypeScript            │
│          Web Dashboard              │
└──────────────────┬──────────────────┘
                   │
                   │ HTTP / REST API
                   ▼
┌─────────────────────────────────────┐
│             FastAPI                 │
│          Backend Services           │
├─────────────────────────────────────┤
│       OR-Tools CP-SAT               │
│       Emergency Scheduling          │
│       Resource Validation           │
│       AI Copilot Integration        │
└──────────────┬───────────┬──────────┘
               │           │
               ▼           ▼
┌────────────────────┐ ┌────────────────────┐
│   MongoDB Atlas    │ │   Google Gemma     │
│   Operational Data │ │   AI Assistance    │
└────────────────────┘ └────────────────────┘
```

---

## Getting Started

Follow these instructions to configure and run SurgiPlan locally.

### Prerequisites

Ensure the following are installed or configured:

- [Git](https://git-scm.com/)
- [Node.js and npm](https://nodejs.org/)
- [Python](https://www.python.org/)
- [MongoDB Atlas](https://www.mongodb.com/atlas) account and database
- Google Gen AI API key, if using the AI Copilot

### 1. Clone the Repository

```bash
git clone https://github.com/DhanushGowdaDev/SurgiPlan.git
cd SurgiPlan
```

### 2. Configure the Backend

Navigate to the backend directory and create a virtual environment.

**Windows PowerShell**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
pip install -r requirements.txt
```

Create a `.env` file inside the `backend` directory:

```env
MONGODB_URI=your_mongodb_connection_string
GEMINI_API_KEY=your_google_genai_api_key
```

Replace the example values with your actual credentials and ensure the variable names match those used by your application.

> **Security:** Never commit `.env` files, database credentials, or API keys to version control.

Start the backend server:

```powershell
python -m uvicorn main:app --reload
```

The backend should be available at:

- **API base URL:** `http://127.0.0.1:8000`
- **Interactive API documentation:** `http://127.0.0.1:8000/docs`

### 3. Configure the Frontend

Open a second terminal from the repository root.

```bash
cd frontend
npm install
```

Configure the frontend API base URL to point to your backend.

For local development:

```text
http://127.0.0.1:8000
```

For production, use your actual deployed backend URL, for example:

```text
https://surgiplan.onrender.com
```

If the API URL is currently hardcoded in `frontend/src/App.tsx`, update it there. For a more maintainable deployment setup, consider using a Vite environment variable such as `VITE_API_URL`.

Start the frontend development server:

```bash
npm run dev
```

Vite will print the local development URL, typically:

`http://localhost:5173`

### 4. Verify the Application

Check backend health:

```text
GET /api/health
```

Check database connectivity:

```text
GET /api/health/database
```

You can test these endpoints through your browser or an API client while the backend is running.

If database-dependent functionality fails, verify your MongoDB Atlas credentials, network access rules, and database configuration.

---

## API Reference

The backend exposes endpoints for health checks, resource retrieval, scheduling, simulation, and AI-assisted interaction.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Check backend health |
| `GET` | `/api/health/database` | Check database connectivity |
| `GET` | `/api/surgeries` | Retrieve surgery records |
| `GET` | `/api/operating-rooms` | Retrieve operating rooms |
| `GET` | `/api/resources` | Retrieve staff and resource data |
| `POST` | `/api/emergency` | Submit an emergency scheduling request |
| `POST` | `/api/schedule/optimize` | Run schedule optimization |
| `POST` | `/api/schedule/simulate` | Simulate a scheduling scenario |
| `GET` | `/api/optimization-history` | Retrieve optimization history |
| `POST` | `/api/copilot` | Submit a request to the AI Copilot |

For endpoint schemas, request parameters, response formats, and interactive testing, start the backend and visit:

`http://127.0.0.1:8000/docs`

*The endpoint list should be verified against the current FastAPI implementation.*

---

## Deployment

SurgiPlan separates its frontend, backend API, and database into independently configured services.

| Component | Platform |
|---|---|
| Frontend | Vercel |
| Backend API | Render |
| Database | MongoDB Atlas |

### Production Configuration

- Configure the frontend to use the deployed backend API URL.
- Store database credentials and AI API keys in backend environment variables.
- Configure CORS to permit requests from trusted frontend origins.
- Verify database connectivity from the deployed backend.
- Test API endpoints after deployment.
- Account for possible cold-start delays on free hosting plans.

---

## Security

Because SurgiPlan addresses hospital operations, security and operational validation are important considerations.

- Keep API keys, passwords, and database connection strings out of source control.
- Use environment variables or a suitable secrets-management solution.
- Apply least-privilege permissions to database users.
- Restrict database network access to trusted sources where feasible.
- Configure CORS for trusted frontend origins.
- Validate incoming requests and handle API errors safely.
- Implement authentication and role-based authorization before exposing sensitive operations.

Avoid using real patient information in development or demonstrations unless the environment and application have been appropriately approved and secured.

---

## Roadmap

Potential future improvements include:

- [ ] Live schedule updates and conflict notifications
- [ ] Advanced emergency rescheduling
- [ ] Detailed optimization metrics and visualizations
- [ ] Enhanced AI-assisted schedule explanations
- [ ] Authentication and role-based access control
- [ ] Comprehensive automated testing
- [ ] Audit logs and operational analytics
- [ ] Expanded scheduling constraints and scenario comparisons

*Roadmap items describe potential future work and are not a statement that these capabilities are currently implemented.*

---

## Disclaimer

SurgiPlan is an operating room scheduling and resource optimization prototype. It does not provide medical diagnoses, treatment recommendations, or clinical decisions.

All schedules and optimization results must be validated by qualified hospital personnel before real-world operational use. The system is not intended to replace clinical judgment, hospital policies, or established safety procedures.

---

## Author

**Dhanush Gowda**

- **GitHub:** [@DhanushGowdaDev](https://github.com/DhanushGowdaDev)
- **Repository:** [DhanushGowdaDev/SurgiPlan](https://github.com/DhanushGowdaDev/SurgiPlan)

---

<p align="center">
  <em>Exploring how constraint programming and AI-assisted interfaces can improve operating room coordination and resource utilization.</em>
</p>
