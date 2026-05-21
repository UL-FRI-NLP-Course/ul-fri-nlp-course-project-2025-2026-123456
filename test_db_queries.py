# DEBUG Script for querying the database and inspecting results
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from src.db.database import get_session, init_db
from src.db.carapi_schema import CarApiCar
from sqlalchemy import func, distinct


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def get_field_names():
    """Print all available fields in the CarApiCar table."""
    fields = [col.name for col in CarApiCar.__table__.columns]
    print(f"Total fields: {len(fields)}\n")
    for i, field in enumerate(fields, 1):
        print(f"{i:2d}. {field}")
    return fields


def get_database_stats(session):
    """Get general statistics about the database."""
    total_cars = session.query(func.count(CarApiCar.id)).scalar()
    total_makes = session.query(func.count(distinct(CarApiCar.make))).scalar()
    total_models = session.query(func.count(distinct(CarApiCar.model))).scalar()
    years = session.query(distinct(CarApiCar.year)).order_by(CarApiCar.year.desc()).all()
    
    print(f"Total records: {total_cars:,}")
    print(f"Unique makes: {total_makes}")
    print(f"Unique models: {total_models}")
    print(f"Year range: {years[-1][0] if years else 'N/A'} - {years[0][0] if years else 'N/A'}")
    

def get_makes_and_count(session):
    """List all makes and number of cars per make."""
    makes = session.query(
        CarApiCar.make,
        func.count(CarApiCar.id).label('count')
    ).group_by(CarApiCar.make).order_by(func.count(CarApiCar.id).desc()).all()
    
    print(f"Total makes: {len(makes)}\n")
    for make, count in makes:
        print(f"  {make:<20} {count:>5} cars")


def print_unique_column_values(label, values):
    print(f"\nUnique {label}:")
    for value in sorted(values)[:10]:
        print(f"  {value}")


def main():
    """Run all test queries."""
    print("\n" + "="*60)
    print("  DATABASE EXPLORATION TOOL")
    print("="*60)
    
    # Initialize database
    init_db()
    session = get_session()
    
    try:
        # 1. Show schema
        print_section("1. DATABASE SCHEMA - All Available Fields")
        get_field_names()
        
        # 2. Database stats
        print_section("2. DATABASE STATISTICS")
        get_database_stats(session)
        
        # 3. Makes
        print_section("3. CAR MAKES AND COUNT")
        get_makes_and_count(session)
        
        # 4. Sample query by make
        print_section("4. SAMPLE QUERY")

        make = "BMW"

        cars = session.query(CarApiCar).filter(
            CarApiCar.make.ilike(make)
        ).all()
        
        if not cars:
            print(f"No cars found for make: {make}")
            return

        print(f"Found {len(cars)} cars for make: {make}")

        unique_models = {car.model for car in cars if car.model}
        unique_series = {car.series for car in cars if car.series}
        unique_trims = {car.trim for car in cars if car.trim}
        unique_submodels = {car.submodel for car in cars if car.submodel}

        print_unique_column_values("models", unique_models)
        print_unique_column_values("series", unique_series)
        print_unique_column_values("trims", unique_trims)
        print_unique_column_values("submodels", unique_submodels)

    finally:
        session.close()




if __name__ == "__main__":
    main()
