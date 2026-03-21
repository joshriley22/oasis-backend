import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import re
from google import genai

app = FastAPI()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Loads API key from Railway
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable not set!")

client = genai.Client(api_key=GEMINI_API_KEY)

# Allows the frontend to call the Backend
# * is used for testing; change to frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Root Route
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}


# Route for your frontend/extension to send data
@app.post("/analyze")
def analyze_product(data: dict):
    product_name = data.get("name")
    print(product_name)
    if not product_name:
        return {"error": "No Product Provided"}

    prompt = f"""
        Product: {product_name}

        Rate this product's sustainability score on a scale from 0-100.
        Only return:
        Score: <number>
        Reason: <short explanation>
        """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",  # ⚡ fast + cheap (best for hackathon)
            contents=prompt
        )
        text = response.text
        match = re.search(r"Score:\s*(\d+)", text)
        score = int(match.group(1)) if match else None
        return {
            "name": product_name,
            "score": score,
            "analysis": text

        }

    except Exception as e:
        return {"error": str(e)}

# Main method for Railway
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # lets Railway provide the port
    # uses FastAPI app "app" hosted on 0.0.0.0 using Railways port, reloading to check for changes for easier development
    uvicorn.run("main:app", host="0.0.0.0", port=port)
