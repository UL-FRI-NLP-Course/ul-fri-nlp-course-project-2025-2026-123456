import os
import sys

import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.config import PDF_ROOT, CARAPI_BASEURL, CARAPI_TOKEN, CARAPI_SECRET

import requests

def get_jwt_token():
    url = f"{CARAPI_BASEURL}/api/auth/login"
    
    payload = {
        "api_token": CARAPI_TOKEN,
        "api_secret": CARAPI_SECRET
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    
    data = response.text.strip()
    return data


def carapi_get_paged_data(url, token, params=None):
    all_data = []
    headers = {"Authorization": f"Bearer {token}"}
    while url:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        all_data.extend(data.get("data", []))
        next_endpoint = data.get("collection").get("next")
        url = f"{CARAPI_BASEURL}{next_endpoint}" if next_endpoint else None
        params = None  # Only use params for the first request
    return all_data

def carapi_request(url, token, params=None):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def download_carapi_data():
    os.makedirs("data/carapi", exist_ok=True)
    brands = os.listdir(PDF_ROOT)

    try:
        token = get_jwt_token()

        for brand in brands:
            print(f"Processing brand: {brand.capitalize()}")
            params = {"make": brand.capitalize()}
            
            trims_path = f"data/carapi/{brand}_trims.json"
            if not os.path.exists(trims_path):
                trims = carapi_get_paged_data(f"{CARAPI_BASEURL}/api/trims/v2", token, params=params)
                with open(trims_path, "w") as f:
                    json.dump(trims, f)
                print(f"  Saved {len(trims)} trims for {brand} to {os.path.basename(trims_path)}")

            bodies_path = f"data/carapi/{brand}_bodies.json"
            if not os.path.exists(bodies_path):
                bodies = carapi_get_paged_data(f"{CARAPI_BASEURL}/api/bodies/v2", token, params=params)
                with open(bodies_path, "w") as f:
                    json.dump(bodies, f)
                print(f"  Saved {len(bodies)} bodies for {brand} to {os.path.basename(bodies_path)}")

            engines_path = f"data/carapi/{brand}_engines.json"
            if not os.path.exists(engines_path):
                engines = carapi_get_paged_data(f"{CARAPI_BASEURL}/api/engines/v2", token, params=params)
                with open(engines_path, "w") as f:
                    json.dump(engines, f)
                print(f"  Saved {len(engines)} engines for {brand} to {os.path.basename(engines_path)}")

            milages_path = f"data/carapi/{brand}_milages.json"
            if not os.path.exists(milages_path):
                milages= carapi_get_paged_data(f"{CARAPI_BASEURL}/api/mileages/v2", token, params=params)
                with open(milages_path, "w") as f:
                    json.dump(milages, f)
                print(f"  Saved {len(milages)} milages for {brand} to {os.path.basename(milages_path)}")

    except requests.exceptions.HTTPError as e:
        print("HTTP error:", e.response.text)
    except Exception as e:
        print("Error:", str(e))

def data_info():
    if not os.path.exists(PDF_ROOT):
        print(f"ERROR: PDF root directory {PDF_ROOT} not found.")
        return

    brand = "BMW"
    with open(f"data/carapi/{brand}_trims.json", "r") as f:
        trims = json.load(f)
    trim_keys = set(trims[0].keys())
    #print(f"Trim keys: {trim_keys}")

    with open(f"data/carapi/{brand}_bodies.json", "r") as f:
        bodies = json.load(f)
    body_keys = set(bodies[0].keys())
    #print(f"Body keys: {body_keys}")

    with open(f"data/carapi/{brand}_engines.json", "r") as f:
        engines = json.load(f)
    engine_keys = set(engines[0].keys())
    #print(f"Engine keys: {engine_keys}")

    with open(f"data/carapi/{brand}_milages.json", "r") as f:
        milages = json.load(f)
    mileage_keys = set(milages[0].keys())
    #print(f"Milage keys: {mileage_keys}")

    shared_keys = trim_keys & body_keys & engine_keys & mileage_keys
    print(f"Shared keys: {shared_keys}\n")

    unique_trim_keys = trim_keys - shared_keys
    unique_body_keys = body_keys - shared_keys
    unique_engine_keys = engine_keys - shared_keys
    unique_mileage_keys = mileage_keys - shared_keys
    print(f"Unique trim keys: {unique_trim_keys}\n")
    print(f"Unique body keys: {unique_body_keys}\n")
    print(f"Unique engine keys: {unique_engine_keys}\n")
    print(f"Unique mileage keys: {unique_mileage_keys}\n")


if __name__ == "__main__":
    download_carapi_data()