from sqlalchemy import Column, Float, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CarApiCar(Base):
    """Flat schema: one row per unique car ID (trim/submodel combo). All measurements in metric."""
    __tablename__ = "carapi_cars"

    id = Column(Integer, primary_key=True)
    
    # Trim fields
    year = Column(Integer)
    make = Column(String)
    model = Column(String)
    series = Column(String)
    submodel = Column(String)
    trim = Column(String)
    description = Column(Text)
    msrp = Column(Float)
    
    # Body fields (metric: cm, liters, kg)
    body_type = Column(String)
    doors = Column(Integer)
    length_cm = Column(Integer)
    width_cm = Column(Integer)
    seats = Column(Integer)
    height_cm = Column(Integer)
    wheel_base = Column(Float)
    front_track = Column(Float)
    rear_track = Column(Float)
    ground_clearance_cm = Column(Float)
    cargo_capacity = Column(Integer)  # liters
    max_cargo_capacity = Column(Integer)  # liters
    curb_weight_kg = Column(Integer)
    gross_weight_kg = Column(Integer)
    max_payload_kg = Column(Float)
    max_towing_capacity_kg = Column(Integer)
    
    # Engine fields
    fuel_type = Column(String)
    cylinders = Column(Integer)
    size = Column(Float)
    horsepower_hp = Column(Integer)
    horsepower_rpm = Column(Integer)
    torque_nm = Column(Integer)
    torque_rpm = Column(Integer)
    valves = Column(Integer)
    valve_timing = Column(String)
    cam_type = Column(String)
    drive_type = Column(String)
    transmission = Column(String)
    engine_type = Column(String)
    
    # Mileage fields
    fuel_tank_capacity = Column(Integer)
    combined_l_per_100km = Column(Float)
    epa_city_l_per_100km = Column(Float)
    epa_highway_l_per_100km = Column(Float)
    range_city_km = Column(Integer)
    range_highway_km = Column(Integer)
    battery_capacity_electric = Column(Float)
    epa_time_to_charge_hr_240v_electric = Column(Float)
    epa_kwh_per_100km_electric = Column(Float)
    range_electric_km = Column(Integer)
    epa_highway_kmpl_electric = Column(Float)
    epa_city_kmpl_electric = Column(Float)
    epa_combined_kmpl_electric = Column(Float)


def init_carapi_db(engine):
    Base.metadata.create_all(bind=engine)