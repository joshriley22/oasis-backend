import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Allow your frontend or extension to call this API
origins = [
    "*",  # For testing only; replace with your frontend URL in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Example route
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}

# Example route for your extension to send data
@app.post("/process")
def process_data(data: dict):
    # Do something with the data
    return {"received": data}

# Main method for Railway
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Railway provides the port
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)