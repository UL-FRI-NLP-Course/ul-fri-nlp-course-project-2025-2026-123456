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

        make = "Toyota"

        cars = session.query(CarApiCar).filter(
        CarApiCar.fuel_type.ilike("electric")
        ).limit(3).all()
        
        if not cars:
            print(f"No cars found for make: {make}")
            return
        
        for car in cars:
            print(f"\n  {car.year} {car.make} {car.model} {car.trim}")
            print(f"    Cargo capacity: {car.cargo_capacity} L")
            print(f"    Cargo capacity (max): {car.max_cargo_capacity} L")
            print(f"    Curb weight: {car.curb_weight_kg} kg")
            print(f"    Gross weight: {car.gross_weight_kg} kg")

            print(f"   Charge time (240V): {car.epa_time_to_charge_hr_240v_electric} hours")
            print(f"    What is this: {car.epa_highway_kmpl_electric} kWh")
            
    finally:
        session.close()


if __name__ == "__main__":
    main()
