from fastapi import FastAPI

app = FastAPI(
    title="SurgiPlan API",
    description="AI-Powered Operating Room Scheduling & Resource Optimization",
    version="0.1.0",
)


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SurgiPlan API",
        "version": "0.1.0",
    }