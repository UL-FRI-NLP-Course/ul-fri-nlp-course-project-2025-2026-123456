import argparse
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import DATA_DIR, EMBEDDING_MODEL, CARAPI_COLUMN_EMBEDDINGS_FILE
from src.db.carapi_schema import CarApiCar
from src.db.database import engine, init_db
from src.db.carapi_column_embeddings import build_and_save_column_embeddings
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker


CARAPI_DIR = os.path.join(DATA_DIR, "carapi")
SessionLocal = sessionmaker(bind=engine)


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as file_handle:
        data = json.load(file_handle)
    return data if isinstance(data, list) else []


def find_brand_files():
    files = {}
    if not os.path.isdir(CARAPI_DIR):
        return files

    for filename in os.listdir(CARAPI_DIR):
        if not filename.endswith(".json"):
            continue

        stem = filename[:-5]
        if "_" not in stem:
            continue

        brand, kind = stem.rsplit("_", 1)
        if kind not in {"trims", "bodies", "engines", "milages"}:
            continue

        path = os.path.join(CARAPI_DIR, filename)
        files.setdefault(brand, {})[kind] = path

    return files


def to_float(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except ValueError:
            return None
    return None


def round_value(val, precision):
    if val is None:
        return None
    if precision == 0:
        return int(round(val))
    return round(val, precision)


def convert_to_metric(record: dict) -> dict:
    # Length/Width/Height: inches -> cm (integer)
    for key in ["length", "width", "height"]:
        val = to_float(record.get(key))
        if val is not None:
            record[f"{key}_cm"] = round_value(val * 2.54, 0)
            del record[key]
    
    # Ground clearance: inches -> cm (2 decimals)
    val = to_float(record.get("ground_clearance"))
    if val is not None:
        record["ground_clearance_cm"] = round_value(val * 2.54, 2)
        del record["ground_clearance"]
    
    # Weight: lbs -> kg (integer for main weights, 2 decimals for payload)
    for key in ["curb_weight", "gross_weight", "max_payload", "max_towing_capacity"]:
        val = to_float(record.get(key))
        if val is not None:
            precision = 0 if key in {"curb_weight", "gross_weight", "max_towing_capacity"} else 2
            record[f"{key}_kg"] = round_value(val * 0.453592, precision)
            del record[key]
    
    # Torque: ft-lbs -> Nm (integer)
    val = to_float(record.get("torque_ft_lbs"))
    if val is not None:
        record["torque_nm"] = round_value(val * 1.35582, 0)
        del record["torque_ft_lbs"]
    
    # Range: miles -> km (integer)
    for key in ["range_city", "range_highway", "range_electric"]:
        val = to_float(record.get(key))
        if val is not None:
            record[f"{key}_km"] = round_value(val * 1.60934, 0)
            del record[key]
    
    # Fuel tank: gallons -> liters (integer)
    val = to_float(record.get("fuel_tank_capacity"))
    if val is not None:
        record["fuel_tank_capacity"] = round_value(val * 3.78541, 0)
    
    # Cargo capacity: cubic feet -> liters (integer)
    for key in ["cargo_capacity", "max_cargo_capacity"]:
        val = to_float(record.get(key))
        if val is not None:
            record[key] = round_value(val * 28.3168, 0)
    
    # MPG -> L/100km (2 decimals)
    for key in ["combined_mpg", "epa_city_mpg", "epa_highway_mpg"]:
        val = to_float(record.get(key))
        if val is not None and val > 0:
            record[key.replace("mpg", "l_per_100km")] = round_value(235.214 / val, 2)
            del record[key]
    
    # Electric MPG -> km/L (2 decimals, just rename)
    for key in ["epa_city_mpg_electric", "epa_highway_mpg_electric", "epa_combined_mpg_electric"]:
        val = to_float(record.get(key))
        if val is not None:
            record[key.replace("mpg", "kmpl")] = round_value(val, 2)
            del record[key]
    
    # kWh/100mi -> kWh/100km (2 decimals)
    val = to_float(record.get("epa_kwh_100_mi_electric"))
    if val is not None:
        record["epa_kwh_per_100km_electric"] = round_value(val / 0.621371, 2)
        del record["epa_kwh_100_mi_electric"]
    
    # Other dimension fields: 2 decimals
    for key in ["wheel_base", "front_track", "rear_track", "size"]:
        if key in record and record[key] is not None:
            record[key] = round_value(to_float(record[key]), 2)
    
    # Other mileage fields: 2 decimals
    for key in ["battery_capacity_electric", "epa_time_to_charge_hr_240v_electric"]:
        if key in record and record[key] is not None:
            record[key] = round_value(to_float(record[key]), 2)
    
    return record


def merge_car_data(trims_list, bodies_dict, engines_dict, milages_dict):
    merged = {}

    for trim in trims_list:
        car_id = trim.get("id")
        if car_id is None:
            continue
        merged[car_id] = dict(trim)

    if isinstance(bodies_dict, dict):
        bodies_iter = bodies_dict.values()
    else:
        bodies_iter = bodies_dict or []

    for body in bodies_iter:
        if not isinstance(body, dict):
            continue
        car_id = body.get("id")
        if car_id is None or car_id not in merged:
            continue
        body_renamed = {("body_type" if k == "type" else k): v for k, v in body.items()}
        body_renamed.pop("trim_id", None)
        merged[car_id].update(body_renamed)

    if isinstance(engines_dict, dict):
        engines_iter = engines_dict.values()
    else:
        engines_iter = engines_dict or []

    for engine_data in engines_iter:
        if not isinstance(engine_data, dict):
            continue
        car_id = engine_data.get("id")
        if car_id is None or car_id not in merged:
            continue
        engine_data_copy = {k: v for k, v in engine_data.items() if k != "trim_id"}
        merged[car_id].update(engine_data_copy)

    if isinstance(milages_dict, dict):
        milages_iter = milages_dict.values()
    else:
        milages_iter = milages_dict or []

    for mileage in milages_iter:
        if not isinstance(mileage, dict):
            continue
        car_id = mileage.get("id")
        if car_id is None or car_id not in merged:
            continue
        mileage_copy = {k: v for k, v in mileage.items() if k != "trim_id"}
        merged[car_id].update(mileage_copy)

    return merged


def ingest_brand(session, brand, files):
    trims_path = files.get("trims")
    bodies_path = files.get("bodies")
    engines_path = files.get("engines")
    milages_path = files.get("milages")

    trims_list = load_json(trims_path) if trims_path else []
    bodies_list = load_json(bodies_path) if bodies_path else []
    engines_list = load_json(engines_path) if engines_path else []
    milages_list = load_json(milages_path) if milages_path else []

    # Convert lists to dicts keyed by ID for easier merging
    bodies_dict = {b.get("id"): b for b in bodies_list if b.get("id")}
    engines_dict = {e.get("id"): e for e in engines_list if e.get("id")}
    milages_dict = {m.get("id"): m for m in milages_list if m.get("id")}

    merged = merge_car_data(trims_list, bodies_dict, engines_dict, milages_dict)

    count = 0
    allowed_cols = {c.name for c in CarApiCar.__table__.columns}

    def normalize_record(record: dict) -> dict:
        record_converted = convert_to_metric(dict(record))
        
        out = {}
        for k, v in record_converted.items():
            if k in allowed_cols:
                out[k] = v
                continue
            # map trim_ prefixed keys (e.g. trim_description -> description)
            if k.startswith("trim_"):
                k2 = k[len("trim_"):]
                if k2 in allowed_cols:
                    out[k2] = v
                    continue

        # BMW data has model/series semantics reversed in source files.
        if brand.lower() in ["bmw", "mercedes-benz"]:
            out["model"], out["series"] = out.get("series"), out.get("model")
        return out

    for car_id, car_data in merged.items():
        try:
            safe_data = normalize_record(car_data)

            if "id" not in safe_data:
                safe_data["id"] = car_id
            session.merge(CarApiCar(**safe_data))
            count += 1
        except Exception as e:
            print(f"  Warning: Failed to insert car ID {car_id}: {e}")

    session.commit()
    return count, len(trims_list)


def rebuild_database(clear=False):
    if clear:
        with engine.begin() as connection:
            connection.execute(text("DROP TABLE IF EXISTS carapi_cars"))
    init_db()


def main():
    parser = argparse.ArgumentParser(description="Ingest CarAPI JSON files into SQLite (flattened to single table).")
    parser.add_argument("--clear", action="store_true", help="Delete existing CarAPI rows before ingesting")
    args = parser.parse_args()

    rebuild_database(clear=args.clear)

    brand_files = find_brand_files()
    if not brand_files:
        print(f"No CarAPI JSON files found in {CARAPI_DIR}")
        return

    session = SessionLocal()
    try:
        total_cars = 0
        for brand, files in sorted(brand_files.items()):
            print(f"Processing {brand}...")
            count, trims_count = ingest_brand(session, brand, files)
            print(f"  Loaded {count}/{trims_count} cars into carapi_cars table")
            total_cars += count

        print(f"\nTotal: {total_cars} cars loaded into carapi_cars")
    finally:
        session.close()


    # Generate column embeddings for Carapi data
    build_and_save_column_embeddings(model_name=EMBEDDING_MODEL, embeddings_path=CARAPI_COLUMN_EMBEDDINGS_FILE, clear=args.clear)
    
if __name__ == "__main__":
    main()