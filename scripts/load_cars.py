"""Load car data from CSV into the SQLite database."""

import csv
import os
import sys
from sqlalchemy import inspect

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.db.database import init_db, get_session
from src.db.models import Car
from src.config import CARS_CSV_PATH


def load_cars_from_csv(csv_path=CARS_CSV_PATH):
	"""Load cars from CSV file into database."""
	if not os.path.exists(csv_path):
		print(f"ERROR: {csv_path} not found")
		return

	init_db()
	session = get_session()

	try:
		# Check if data already loaded
		count = session.query(Car).count()
		if count > 0:
			print(f"Database already has {count} cars. Skipping load.")
			return

		with open(csv_path, 'r', encoding='utf-8') as f:
			reader = csv.DictReader(f)
			cars_added = 0

			for row in reader:
				car = Car(
					brand=row.get('brand'),
					model=row.get('model'),
					price_min=float(row.get('price_min', 0)),
					price_max=float(row.get('price_max', 0)),
					fuel_type=row.get('fuel_type'),
					body_type=row.get('body_type'),
					seats=int(row.get('seats', 5)) if row.get('seats') else 5,
					transmission=row.get('transmission'),
					horsepower=int(row.get('horsepower', 0)) if row.get('horsepower') else 0,
					torque=int(row.get('torque', 0)) if row.get('torque') else 0,
					fuel_consumption=float(row.get('fuel_consumption', 0)) if row.get('fuel_consumption') else 0,
					co2_emissions=float(row.get('co2_emissions', 0)) if row.get('co2_emissions') else 0,
					width=float(row.get('width', 0)) if row.get('width') else 0,
					length=float(row.get('length', 0)) if row.get('length') else 0,
					height=float(row.get('height', 0)) if row.get('height') else 0,
					weight=int(row.get('weight', 0)) if row.get('weight') else 0,
					trunk_volume=int(row.get('trunk_volume', 0)) if row.get('trunk_volume') else 0,
					has_awd=row.get('has_awd', 'false').lower() == 'true',
					safety_rating=float(row.get('safety_rating', 0)) if row.get('safety_rating') else 0,
					year=int(row.get('year', 2025)) if row.get('year') else 2025,
					in_stock=row.get('in_stock', 'true').lower() == 'true',
				)
				session.add(car)
				cars_added += 1

		session.commit()
		print(f"Loaded {cars_added} cars into database from {csv_path}")

	except Exception as e:
		session.rollback()
		print(f"Error loading cars: {e}")
		raise

	finally:
		session.close()


if __name__ == "__main__":
	load_cars_from_csv()
