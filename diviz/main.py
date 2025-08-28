from fastapi import FastAPI, Query, HTTPException, Body
from typing import Optional

from diviz.user import User

# Create FastAPI app instance
app = FastAPI(
    title="DiViz API",
    description="A meeting efficiency review API service",
    version="0.0.1"
)


@app.get("/")
async def root():
    """
    Root endpoint with basic service information.
    """
    return {
        "service": "DiViz API Service",
        "version": "0.0.1",
        "endpoints": {
            "/review": "GET - meeting review"
        }
    }

users = []

@app.post("/users")
async def create_user(user: User = Body(..., description="User information")):
    users.append(user)
    return {"message": "User created", "total_users": len(users)}


@app.get("/review/gmeet/{google_meet}")
async def review(google_meet: str):
    return {"meeting_code": google_meet}


def main():
    """Main entry point for the application."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
