from src.db.queries import query_cars_by_constraints
from src.db.database import get_session
from src.db.models import Car

session = get_session()
new_car = Car(
    brand="Tesla",
    model="Model 3",
    price_min=45000,
    price_max=55000,
    fuel_type="electric",
    body_type="sedan",
    seats=5,
    transmission="automatic",
    horsepower=358,
    safety_rating=4.7,
    year=2025,
)
session.add(new_car)
session.commit()
session.close()