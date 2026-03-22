import sys
print(f"Python version: {sys.version}", flush=True)
print("Starting backend...", flush=True)
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import re
print("Before import", flush=True)
from google import genai
print("After import", flush=True)
app = FastAPI()
cache = {}
print("App file imported successfully", flush=True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Loads API key from Railway
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable not set!")
print("Gemini key set", flush=True)
client = genai.Client(api_key=GEMINI_API_KEY)
print("client set", flush=True)

# Allows the frontend to call the Backend
# * is used for testing; change to frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("middleware set", flush=True)



# Root Route
@app.get("/")
def read_root():
    print("root ran", flush=True)
    return {"message": "Hello from FastAPI!"}
print("root set", flush=True)


# Route for your frontend/extension to send data
@app.post("/analyze")
def analyze_product(data: dict):
    product_name = data.get("product")
    print(product_name, flush=True)
    if not product_name:
        return {"error": "No product provided"}
    product_name = product_name.lower().strip()
    print(product_name)
    if product_name in cache:
        print("Cache hit")
        return cache[product_name]
    print("Cache miss")
    prompt = f"""
        You are an expert in environmental sustainability.
        Evaluate the sustainability of the following product:
        Product: {product_name}
        Score the product from 0 to 100 based on:
        - Environmental impact of materials
        - Carbon footprint of production and transport
        - Packaging sustainability
        - Reusability or recyclability
        Also include a url to a more eco-friendly alternative product on the same website.
        
        Scoring guidelines:
        - 0–30: harmful to environment
        - 33–67: slightly harmful to environment
        - 67–100: Highly sustainable
        
        
        Respond in EXACT format:
        Score: <number from 0 to 100>
        Reason: <1-3 sentence explanation>
        Alternative: <url to more eco-friendly alternative product on the same website>
        """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",  # ⚡ fast + cheap (best for hackathon)
            contents=prompt
        )
        text = response.text
        if not text:
            return {"error": "Empty response from Gemini"}
        match = re.search(r"Score:\s*(\d+)", text) or re.search(r"\d+", text)
        if match:
            score = int(match.group(1)) if match.lastindex else int(match.group(0))
        else:
            score = None

        if score is not None:
            score = max(0, min(score, 100))
        result = {
            "name": product_name,
            "score": score,
            "analysis": text,
            "link": text
        }
        cache[product_name] = result
        return result
    except Exception as e:
        return {"error": str(e)}
print("analyize set", flush=True)
# Runs file locally
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # lets Railway provide the port
    # uses FastAPI app "app" hosted on 0.0.0.0 using Railways port, reloading to check for changes for easier development
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload = False)
