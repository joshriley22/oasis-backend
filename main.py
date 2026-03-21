import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests

app = FastAPI()

# Read your Gemini API key from environment
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable not set!")

# Allow your frontend to call this API
origins = [
    "*"  # For testing only; replace with your frontend URL in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Example root route
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}

# Route that calls Gemini API securely
@app.get("/gemini/ticker")
def get_gemini_ticker():
    url = "https://api.gemini.com/v1/pubticker/btcusd"  # Example public endpoint
    headers = {"X-GEMINI-APIKEY": API_KEY}  # Private endpoints require this
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
    return response.json()

# Route for your frontend/extension to send data
@app.post("/process")
def process_data(data: dict):
    # Do something with the data
    return {"received": data}

# Main method for Railway
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Railway provides the port
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)