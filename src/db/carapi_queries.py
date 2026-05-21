import random

from sqlalchemy import inspect, text

import sys
import os

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.db.database import engine


def _normalize_constraint_name(name: str) -> str:
    return (name or "").strip().lower()


def _build_constraint_clause(constraint: dict, params: dict, index: int):
    name = constraint.get("name")
    value = constraint.get("value")
    op = _normalize_constraint_name(constraint.get("constraint"))

    if not name or op in {"", "none", "null"}:
        return None

    column = _normalize_constraint_name(name)

    if value is None:
        return None

    param_name = f"{column}_{index}"

    if op == "equal":
        # support list-valued equals -> IN clause
        if isinstance(value, (list, tuple)):
            placeholders = []
            for i, v in enumerate(value):
                key = f"{param_name}_{i}"
                placeholders.append(f":{key}")
                params[key] = v.lower() if isinstance(v, str) else v
            if all(isinstance(v, str) for v in value):
                return f"LOWER(COALESCE({column}, '')) IN ({', '.join(placeholders)})"
            else:
                return f"{column} IN ({', '.join(placeholders)})"

        params[param_name] = value.lower() if isinstance(value, str) else value
        return f"LOWER(COALESCE({column}, '')) = :{param_name}" if isinstance(value, str) else f"{column} = :{param_name}"

    if op == "min":
        params[param_name] = value
        return f"COALESCE({column}, 0) >= :{param_name}"

    if op == "max":
        params[param_name] = value
        return f"COALESCE({column}, 0) <= :{param_name}"

    if op == "range" and isinstance(value, (list, tuple)) and len(value) == 2:
        low_name = f"{column}_{index}_low"
        high_name = f"{column}_{index}_high"
        params[low_name] = value[0]
        params[high_name] = value[1]
        return f"COALESCE({column}, 0) BETWEEN :{low_name} AND :{high_name}"

    return None

def row_to_car_dict(row):
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


def fetch_car_rows(where_clause="", params=None, limit=20):
    params = dict(params or {})
    params["limit"] = limit

    sql = "SELECT * FROM carapi_cars"
    if where_clause:
        sql += f" WHERE {where_clause}"
    sql += " ORDER BY year DESC, msrp ASC LIMIT :limit"

    with engine.connect() as connection:
        result = connection.execute(text(sql), params)
        return [row_to_car_dict(row) for row in result.mappings()]


def build_filter_clauses(constraints: list[dict]):
    filtered = []
    for c in constraints:
        name = c.get("name")
        value = c.get("value")

        if not name or value is None:
            continue

        column = _normalize_constraint_name(name)

        if isinstance(value, (list, tuple)):
            valid_values = [v for v in value if value_exists_in_column(column, v)]
            if valid_values:
                filtered.append({"name": column, "value": valid_values, "constraint": c.get("constraint")})
        else:
            if value_exists_in_column(column, value):
                filtered.append({"name": column, "value": value, "constraint": c.get("constraint")})

    clauses = []
    params = {}
    for index, constraint in enumerate(filtered):
        clause = _build_constraint_clause(constraint, params, index)
        if clause:
            clauses.append(clause)

    return clauses, params


def group_unique_models(rows):
    seen = set()
    unique_models = []

    for row in rows:
        brand = row.get("brand")
        model = row.get("model")
        if not brand or not model:
            continue

        key = (str(brand).strip().lower(), str(model).strip().lower())
        if key in seen:
            continue

        seen.add(key)
        unique_models.append({"brand": brand, "model": model})

    return unique_models


def value_exists_in_column(column_name: str, value) -> bool:
    inspector = inspect(engine)
    valid_columns = {column["name"] for column in inspector.get_columns("carapi_cars")}

    if column_name not in valid_columns:
        return False

    if value is None:
        return False

    if isinstance(value, str):
        sql = text(
            f'SELECT 1 FROM carapi_cars WHERE LOWER(COALESCE("{column_name}", "")) = :value LIMIT 1'
        )
        params = {"value": value.strip().lower()}
    else:
        sql = text(f'SELECT 1 FROM carapi_cars WHERE "{column_name}" = :value LIMIT 1')
        params = {"value": value}

    with engine.connect() as connection:
        result = connection.execute(sql, params).first()
        return result is not None


def query_carapi_by_constraints(constraints: list[dict], limit=20, unique_models=True):
    if unique_models:
        return query_unique_models_by_constraints(constraints, limit=limit)
    
    clauses, params = build_filter_clauses(constraints)
    where_clause = " AND ".join(clauses)
    return fetch_car_rows(where_clause=where_clause, params=params, limit=limit)


def query_unique_models_by_constraints(constraints: list[dict], limit=20):
    clauses, params = build_filter_clauses(constraints)
    where_clause = " AND ".join(clauses)

    sql = "SELECT DISTINCT make AS brand, model FROM carapi_cars"
    if where_clause:
        sql += f" WHERE {where_clause}"
    sql += " ORDER BY make ASC, model ASC LIMIT :limit"

    params = dict(params or {})
    params["limit"] = limit

    with engine.connect() as connection:
        result = connection.execute(text(sql), params)
        return [{"brand": row[0], "model": row[1]} for row in result.fetchall()]



def get_carapi_by_id(car_id: int):
    cars = fetch_car_rows(where_clause="id = :car_id", params={"car_id": car_id}, limit=1)
    return cars[0] if cars else None


def get_all_carapi_cars(limit=100):
    return fetch_car_rows(limit=limit)


def cars_to_dicts(cars):
    return list(cars)


def get_unique_values_from_column(column_name: str, limit: int = None):
    inspector = inspect(engine)
    valid_columns = {column["name"] for column in inspector.get_columns("carapi_cars")}

    if column_name not in valid_columns:
        raise ValueError(f"Unknown column: {column_name}")

    sql = text(
        f'SELECT DISTINCT "{column_name}" AS value FROM carapi_cars WHERE "{column_name}" IS NOT NULL'
    )

    with engine.connect() as connection:
        result = connection.execute(sql)
        unique_values = [row[0] for row in result if row[0] is not None]

    if limit is None:
        return unique_values

    if limit >= len(unique_values):
        return unique_values

    return random.sample(unique_values, limit)


if __name__ == "__main__":
    constraints = [
        {'name': 'make', 'value': ['BMW', 'Mercedes'], 'constraint': 'equal'},
        {'name': 'model', 'value': None, 'constraint': None},
        {'name': 'msrp', 'value': [50000, 60000], 'constraint': 'range'}, 
        {'name': 'body_type', 'value': 'coupe', 'constraint': 'equal'}
    ]

    constraints2 = [
        {'name': 'seats', 'value': 7, 'constraint': 'equal'},
        {'name': 'body_type', 'value': 'SUV', 'constraint': 'equal'},
    ]

    cars = query_unique_models_by_constraints(constraints2)
    for car in cars:
        print(car)