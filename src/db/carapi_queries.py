from sqlalchemy import text

from src.db.database import engine



def _row_to_car_dict(row):
    return {
        "id": row["id"],
        "brand": row["make"],
        "model": row["model"],
        "year": row["year"],
        "trim": row["trim"],
        "series": row["series"],
        "submodel": row["submodel"],
        "msrp": row["msrp"],
        "fuel_type": row["fuel_type"],
        "body_type": row["body_type"],
        "seats": row["seats"],
        "transmission": row["transmission"],
        "horsepower": row["horsepower_hp"],
        "torque_nm": row["torque_nm"],
        "fuel_consumption_l_per_100km": row["combined_l_per_100km"],
        "width_cm": row["width_cm"],
        "length_cm": row["length_cm"],
        "height_cm": row["height_cm"],
        "weight_kg": row["curb_weight_kg"],
        "trunk_volume": row["cargo_capacity"],
        "has_awd": (row["drive_type"] or "").lower() in {"awd", "4wd", "4x4"},
        "faiss_score": 0.0,
    }


def _fetch_car_rows(where_clause="", params=None, limit=20):
    params = dict(params or {})
    params["limit"] = limit

    sql = "SELECT * FROM carapi_cars"
    if where_clause:
        sql += f" WHERE {where_clause}"
    sql += " ORDER BY year DESC, msrp ASC LIMIT :limit"

    with engine.connect() as connection:
        result = connection.execute(text(sql), params)
        return [_row_to_car_dict(row) for row in result.mappings()]


def query_carapi_by_constraints(parsed_query: dict, limit=20):
    clauses = []
    params = {}

    budget_max = parsed_query.get("budget_max")
    if budget_max is not None:
        clauses.append("COALESCE(msrp, 0) <= :budget_max")
        params["budget_max"] = budget_max

    fuel_types = parsed_query.get("fuel_types", [])
    if fuel_types:
        placeholders = []
        for index, fuel_type in enumerate(fuel_types):
            key = f"fuel_{index}"
            placeholders.append(f":{key}")
            params[key] = fuel_type.lower()
        clauses.append(f"LOWER(COALESCE(fuel_type, '')) IN ({', '.join(placeholders)})")

    body_styles = parsed_query.get("body_styles", [])
    if body_styles:
        placeholders = []
        for index, body_style in enumerate(body_styles):
            key = f"body_{index}"
            placeholders.append(f":{key}")
            params[key] = body_style.lower()
        clauses.append(f"LOWER(COALESCE(body_type, '')) IN ({', '.join(placeholders)})")

    seating_min = parsed_query.get("seating_min")
    if seating_min is not None:
        clauses.append("COALESCE(seats, 0) >= :seating_min")
        params["seating_min"] = seating_min

    transmission = parsed_query.get("transmission")
    if transmission:
        clauses.append("LOWER(COALESCE(transmission, '')) = :transmission")
        params["transmission"] = transmission.lower()

    where_clause = " AND ".join(clauses)
    return _fetch_car_rows(where_clause=where_clause, params=params, limit=limit)


def get_carapi_by_id(car_id: int):
    cars = _fetch_car_rows(where_clause="id = :car_id", params={"car_id": car_id}, limit=1)
    return cars[0] if cars else None


def get_all_carapi_cars(limit=100):
    return _fetch_car_rows(limit=limit)


def cars_to_dicts(cars):
    return list(cars)
