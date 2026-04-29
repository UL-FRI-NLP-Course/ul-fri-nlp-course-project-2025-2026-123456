from sqlalchemy import Column, Integer, String, Float, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True)
    brand = Column(String, nullable=False)  # e.g., "Audi"
    model = Column(String, nullable=False)  # e.g., "A4"
    price_min = Column(Float, nullable=False)  # Min price in euros
    price_max = Column(Float, nullable=False)  # Max price in euros
    fuel_type = Column(String, nullable=False)  # "petrol", "diesel", "hybrid", "electric"
    body_type = Column(String, nullable=False)  # "sedan", "suv", "hatchback", etc.
    seats = Column(Integer)  # Number of seats
    transmission = Column(String)  # "manual", "automatic"
    horsepower = Column(Integer)  # Engine power
    torque = Column(Integer)  # Torque
    fuel_consumption = Column(Float)  # L/100km
    co2_emissions = Column(Float)  # g/km
    width = Column(Float)  # Vehicle width (mm)
    length = Column(Float)  # Vehicle length (mm)
    height = Column(Float)  # Vehicle height (mm)
    weight = Column(Integer)  # Curb weight (kg)
    trunk_volume = Column(Integer)  # Trunk volume (L)
    has_awd = Column(Boolean, default=False)
    safety_rating = Column(Float)  # e.g., 4.5/5
    comfort_features = Column(JSON)  # {"leather": true, "sunroof": false}
    year = Column(Integer)  # Model year

    def __repr__(self):
        return f"<Car {self.brand} {self.model} {self.year}>"