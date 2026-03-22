
import json
import os
import re
import urllib.error
import urllib.request

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

print("Starting backend...", flush=True)

app = FastAPI()
cache = {}

print("App file imported successfully", flush=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable not set!")

print("Gemini key set", flush=True)

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


def call_gemini(prompt: str) -> str:
    """
    Calls Gemini REST API directly using the standard library.
    This avoids dependency issues with unavailable SDK packages.
    """
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
            parsed = json.loads(body)

            candidates = parsed.get("candidates", [])
            if not candidates:
                return ""

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            text_parts = [
                part.get("text", "")
                for part in parts
                if isinstance(part, dict)
            ]
            return "\n".join(text_parts).strip()

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Gemini API HTTP error {e.code}: {error_body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Gemini API connection error: {e.reason}") from e


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
    print(product_name, flush=True)

    if product_name in cache:
        print("Cache hit", flush=True)
        return cache[product_name]

    print("Cache miss", flush=True)

    prompt = f"""
Product: {product_name}

Rate this product's sustainability score on a scale from 0-100.
Only return:
Score: <number from 0 to 100>
Reason: <short explanation>
""".strip()

    try:
        text = call_gemini(prompt)

        if not text:
            return {"error": "Empty response from Gemini"}

        score_match = re.search(r"Score:\s*(\d{1,3})", text)
        if score_match:
            score = int(score_match.group(1))
        else:
            any_number_match = re.search(r"\b(\d{1,3})\b", text)
            score = int(any_number_match.group(1)) if any_number_match else None

        if score is not None:
            score = max(0, min(score, 100))

        result = {
            "name": product_name,
            "score": score,
            "analysis": text,
        }
        cache[product_name] = result
        return result

    except Exception as e:
        return {"error": str(e)}

print("analyze route set", flush=True)

# Runs file locally
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
