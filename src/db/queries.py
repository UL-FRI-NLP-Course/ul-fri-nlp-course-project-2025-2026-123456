from sqlalchemy import and_, or_, func
from src.db.database import get_session
from src.db.models import Car


def query_cars_by_constraints(parsed_query: dict, limit=20):
	"""Query database for cars matching parsed query constraints.

	Filters by:
	- budget_max: price must be <= budget
	- fuel_types: one of the specified fuel types
	- body_styles: one of the specified body types
	- seating_min: seats >= seating_min
	- transmission: exact match

	Returns list of Car ORM objects sorted by relevance.
	"""
	session = get_session()

	try:
		query_obj = session.query(Car)

		budget_max = parsed_query.get("budget_max")
		if budget_max is not None:
			query_obj = query_obj.filter(Car.price_max <= budget_max)

		fuel_types = parsed_query.get("fuel_types", [])
		if fuel_types:
			query_obj = query_obj.filter(Car.fuel_type.in_(fuel_types))

		body_styles = parsed_query.get("body_styles", [])
		if body_styles:
			query_obj = query_obj.filter(Car.body_type.in_(body_styles))

		seating_min = parsed_query.get("seating_min")
		if seating_min is not None:
			query_obj = query_obj.filter(Car.seats >= seating_min)

		transmission = parsed_query.get("transmission")
		if transmission:
			query_obj = query_obj.filter(Car.transmission == transmission)

		results = query_obj.order_by(Car.price_min).limit(limit).all()
		return results

	finally:
		session.close()


def get_car_by_id(car_id: int):
	session = get_session()
	try:
		return session.query(Car).filter(Car.id == car_id).first()
	finally:
		session.close()


def get_all_cars(limit=100):
	session = get_session()
	try:
		return session.query(Car).filter(Car.in_stock == True).limit(limit).all()
	finally:
		session.close()


def cars_to_dicts(cars):
	return [
		{
			"id": c.id,
			"brand": c.brand,
			"model": c.model,
			"price_min": c.price_min,
			"price_max": c.price_max,
			"fuel_type": c.fuel_type,
			"body_type": c.body_type,
			"seats": c.seats,
			"transmission": c.transmission,
			"horsepower": c.horsepower,
			"fuel_consumption": c.fuel_consumption,
			"safety_rating": c.safety_rating,
			"width": c.width,
			"length": c.length,
			"height": c.height,
			"weight": c.weight,
			"trunk_volume": c.trunk_volume,
			"has_awd": c.has_awd,
			"year": c.year,
		}
		for c in cars
	]
