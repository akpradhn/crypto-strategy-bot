import pytz
from fastapi import FastAPI, Query, HTTPException
from datetime import datetime
import hashlib
from recommendations.recommender_onfly import generate_crypto_recommendations

app = FastAPI(title="Crypto Recommendation API")

STORED_HASHED_KEY = "40b879f9d82a20b7c73d45a373d8f55e0761fd871dd26bd756ab54704dd13976"

def is_valid_api_key(provided_key: str) -> bool:
    return hashlib.sha256(provided_key.encode()).hexdigest() == STORED_HASHED_KEY

@app.get("/recommendation")
def get_recommendation(
    api_key: str = Query(...),
    scrapping_interval: str = Query("1m"),
    look_back: int = Query(180),
    trade_margin: float = Query(1.0),
    coin: str = Query("BTC")
):
    if not is_valid_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API Key")

    request_body = {
        "SCRAPPING_INTERVAL": scrapping_interval,
        "LOOK_BACK": look_back,
        "TRADE_MARGIN": trade_margin,
        "CURRENT_TIME": datetime.now(pytz.timezone("Asia/Kolkata")),
        "COIN":coin
    }

    recommendation = generate_crypto_recommendations(request_body)

    return {"status": "success","config":request_body, "data": recommendation}


