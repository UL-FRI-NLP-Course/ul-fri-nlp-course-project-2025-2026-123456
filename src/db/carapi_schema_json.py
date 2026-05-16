import json
from math import isfinite

from sqlalchemy import text

import sys
import os

src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
repo_root = os.path.abspath(os.path.join(src_dir, ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from db.database import engine
from db.carapi_schema import CarApiCar

def create_carapi_schema_json(threshold_unique=50, frac_threshold=0.1, sample_limit=1000):
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM carapi_cars")).scalar() or 0

        cols = [c.name for c in CarApiCar.__table__.columns]
        summary = {}
    
        drop_fields = {
            "description",
            "front_track",
            "rear_track",
            "max_cargo_capacity",
            "gross_weight_kg",
            "horsepower_rpm",
            "torque_rpm",
            "valves",
            "valve_timing",
            "cam_type",
            "epa_city_l_per_100km",
            "epa_highway_l_per_100km",
            "range_city_km",
            "range_highway_km",
            "battery_capacity_electric",
            "epa_time_to_charge_hr_240v_electric",
            "epa_kwh_per_100km_electric",
            "range_electric_km",
            "epa_highway_kmpl_electric",
            "epa_city_kmpl_electric",
            "epa_combined_kmpl_electric",
        }

        def examples_from_different_makes(column, max_examples=3):
            makes = [r[0] for r in conn.execute(text("SELECT DISTINCT make FROM carapi_cars WHERE make IS NOT NULL ORDER BY make")).fetchall()]
            examples = []
            for make in makes:
                val = conn.execute(text(f"SELECT {column} FROM carapi_cars WHERE make = :make AND {column} IS NOT NULL LIMIT 1"), {"make": make}).scalar()
                if val is not None:
                    examples.append(str(val).strip())
                if len(examples) >= max_examples:
                    break
            return examples

        for col in cols:
            if col in drop_fields:
                continue

            col_obj = CarApiCar.__table__.columns[col]
            type_name = col_obj.type.__class__.__name__

            # too many unique values, just add 3 examples 
            if col in {"model", "series", "trim", "submodel"}:
                examples = examples_from_different_makes(col, max_examples=3)
                examples.append("...")
                summary[col] = examples if examples else "string"
                continue

            if type_name in ("String", "Text"):
                distinct = conn.execute(text(f"SELECT COUNT(DISTINCT {col}) FROM carapi_cars")).scalar() or 0

                if (distinct <= threshold_unique) or (total and distinct / total <= frac_threshold):
                    rows = conn.execute(text(f"SELECT DISTINCT {col} FROM carapi_cars WHERE {col} IS NOT NULL ORDER BY {col} LIMIT :limit"), {"limit": sample_limit})
                    vals = [r[0] for r in rows.fetchall()]
                    vals = [str(v).strip() for v in vals if v is not None]
                    vals = sorted(set(vals))
                    summary[col] = vals
                else:
                    summary[col] = "string"

            elif type_name == "Integer":
                summary[col] = "int"
            elif type_name == "Float":
                summary[col] = "float"
            else:
                summary[col] = type_name.lower()

        return summary
