# 🏥 SurgiPlan
### AI-Powered Operating Room Scheduling & Resource Optimization

**Optimize every operating room. Adapt to every change.**

SurgiPlan is an intelligent operating room scheduling and resource optimization platform designed to help hospitals coordinate surgical procedures, operating rooms, medical staff, equipment, and recovery beds.

It combines constraint-based optimization with AI-powered natural-language assistance to support scheduling decisions and respond to operational changes.

> **Core principle:** OR-Tools is the source of truth for scheduling. Gemma supports natural-language understanding, schedule explanations, and what-if scenario interpretation.

---

## ✨ Features

- **Intelligent Scheduling** — Optimize operating room assignments and surgery start times using Google OR-Tools CP-SAT.
- **Emergency Scheduling** — Submit emergency cases and evaluate scheduling feasibility against existing operational constraints.
- **Resource Management** — Track surgeries, operating rooms, staff, equipment, and recovery-bed requirements.
- **Constraint-Aware Optimization** — Account for surgery duration, staff availability, equipment capacity, room suitability, and recovery resources.
- **Schedule Simulation** — Explore operational scenarios and assess their potential impact on the schedule.
- **AI Copilot** — Use natural language to ask scheduling questions, understand constraints, and interpret what-if scenarios.
- **Optimization History** — Review recorded optimization results when available.
- **Web Dashboard** — Monitor hospital operations through a React-based interface.

## 🧠 How It Works

SurgiPlan separates optimization from AI assistance to keep scheduling logic reliable and explainable.

1. **Input:** Load surgical cases, operating rooms, staff, equipment, and recovery requirements.
2. **Model:** Represent scheduling requirements as constraints.
3. **Optimize:** Use OR-Tools CP-SAT to search for a feasible, optimized schedule.
4. **Evaluate:** Check resource conflicts and scheduling feasibility.
5. **Explain:** Use the AI Copilot to help interpret requests and explain scheduling outcomes.

**OR-Tools determines the schedule.** The AI Copilot assists with language and explanations; it does not replace the optimization solver.

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Styling | Tailwind CSS |
| Backend | Python, FastAPI |
| Optimization Engine | Google OR-Tools CP-SAT |
| AI Assistance | Google Gemma / Google Gen AI SDK |
| Database | MongoDB Atlas |
| Charts | Recharts |
| Frontend Hosting | Vercel |
| Backend Hosting | Render |
| Version Control | Git and GitHub |

## 🏗️ Architecture

```text
┌───────────────────────────────┐
│       React + TypeScript      │
│         Web Dashboard         │
└──────────────┬────────────────┘
               │ HTTP / REST API
               ▼
┌───────────────────────────────┐
│          FastAPI              │
│       Backend Services        │
├───────────────────────────────┤
│  OR-Tools CP-SAT Optimizer    │
│  Emergency Scheduling         │
│  Resource Validation          │
│  AI Copilot Integration       │
└───────────┬───────────┬───────┘
            │           │
            ▼           ▼
┌─────────────────┐  ┌─────────────────┐
│  MongoDB Atlas  │  │  Google Gemma   │
│ Operational Data│  │ Language Support│
└─────────────────┘  └─────────────────┘
```

## 🚀 Getting Started

### Prerequisites

Install the following before running SurgiPlan locally:

- Node.js and npm
- Python
- Git
- A MongoDB Atlas account and database
- A Google Gen AI API key if using the AI Copilot

### 1. Clone the repository

```bash
git clone https://github.com/DhanushGowdaDev/SurgiPlan.git
cd SurgiPlan
```

### 2. Configure the backend

Create and activate a virtual environment:

**Windows PowerShell**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create a `.env` file inside the `backend` directory using the environment variable names expected by the application:

```env
MONGODB_URI=your_mongodb_connection_string
GEMINI_API_KEY=your_google_genai_api_key
```

Replace the example values with your own credentials. Never commit `.env` files or expose API keys in frontend code.

Start the backend:

```powershell
python -m uvicorn main:app --reload
```

Backend URL: `http://127.0.0.1:8000`

Interactive API documentation: `http://127.0.0.1:8000/docs`

### 3. Configure the frontend

Open a second terminal from the repository root:

```bash
cd frontend
npm install
```

The frontend must point to the backend URL. For local development, the API base URL in `frontend/src/App.tsx` can be:

```typescript
const API = "http://127.0.0.1:8000";
```

For production, use the deployed backend URL:

```typescript
const API = "https://surgiplan.onrender.com";
```

Start the frontend:

```bash
npm run dev
```

Vite will print the local development URL in the terminal, usually `http://localhost:5173`.

### 4. Verify the application

Check the backend health endpoint:

```text
http://127.0.0.1:8000/api/health
```

Check database connectivity:

```text
http://127.0.0.1:8000/api/health/database
```

Ensure MongoDB Atlas network access, credentials, and database configuration are correct before testing database-dependent features.

## 📡 API Endpoints

The backend exposes the following API routes:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check backend health |
| GET | `/api/health/database` | Check database connectivity |
| GET | `/api/surgeries` | Retrieve surgery records |
| GET | `/api/operating-rooms` | Retrieve operating rooms |
| GET | `/api/resources` | Retrieve staff and resource data |
| POST | `/api/emergency` | Submit an emergency scheduling request |
| POST | `/api/schedule/optimize` | Run schedule optimization |
| POST | `/api/schedule/simulate` | Simulate a scheduling scenario |
| GET | `/api/optimization-history` | Retrieve optimization history |
| POST | `/api/copilot` | Send a request to the AI Copilot |

For request schemas and interactive testing, visit the FastAPI `/docs` endpoint.

## ☁️ Deployment

SurgiPlan uses separate hosting services for its frontend and backend.

| Component | Platform |
|---|---|
| Frontend | Vercel |
| Backend API | Render |
| Database | MongoDB Atlas |

The production frontend connects to the Render API. Keep database credentials and AI API keys in backend environment variables, not in the frontend.

Free hosting plans may introduce cold-start delays. Database access rules and CORS must be configured appropriately for production.

## 🔐 Security Considerations

- Keep API keys, passwords, and database connection strings out of Git.
- Use environment variables for secrets.
- Apply least-privilege permissions to MongoDB database users.
- Restrict MongoDB network access to trusted sources where feasible.
- Configure CORS to allow only trusted frontend origins.
- Validate scheduling requests and handle API errors safely.

## 🗺️ Roadmap

Potential future improvements include:

- [ ] Live schedule updates and conflict notifications
- [ ] Enhanced emergency rescheduling
- [ ] More detailed optimization metrics and visualizations
- [ ] Improved schedule explanations through the AI Copilot
- [ ] Authentication and role-based access control
- [ ] Comprehensive automated testing
- [ ] Audit logs and operational analytics
- [ ] Expanded scheduling constraints and scenario comparisons

## ⚠️ Disclaimer

SurgiPlan is an operations scheduling and resource optimization prototype. It does **not** provide medical diagnosis, treatment recommendations, or clinical decisions.

Schedules and optimization results require validation by qualified hospital personnel before real-world operational use. The system is not intended to replace clinical judgment, hospital policies, or established safety procedures.

## 👨‍💻 Author

**Dhanush Gowda**

GitHub: [@DhanushGowdaDev](https://github.com/DhanushGowdaDev)

**Repository:** [DhanushGowdaDev/SurgiPlan](https://github.com/DhanushGowdaDev/SurgiPlan)

---

*Built to explore how constraint programming and AI-assisted interfaces can improve hospital operating room coordination.*
