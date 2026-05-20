from sqlalchemy import Column, Float, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

from dataclasses import dataclass, field
from typing import List, Optional, Dict

Base = declarative_base()

class CarApiCar(Base):
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


@dataclass
class ColumnMetadata:
    name: str
    display_name: str

    description: str

    user_intents: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    related_terms: List[str] = field(default_factory=list)

    units: Optional[str] = None
    value_type: Optional[str] = None

    example_queries: List[str] = field(default_factory=list)

    # generates from the database values
    sample_values: List[str] = field(default_factory=list)
    sample_size: int = 3 # None == all unique values


CARAPI_SCHEMA_METADATA: Dict[str, ColumnMetadata] = {

    "year": ColumnMetadata(
        name="year",
        display_name="Model Year",
        description="Vehicle production or model year.",
        user_intents=[
            "newer cars",
            "older vehicles",
            "cars after 2020",
            "2018 model"
        ],
        synonyms=[
            "year",
            "model year",
            "production year"
        ],
        related_terms=[
            "new",
            "old",
            "latest generation", 
            "redesign",
            "facelift"
        ],
        value_type="integer",
        example_queries=[
            "bmw after 2020",
            "2019 suv",
            "newer than 2018"
        ]
    ),

    "make": ColumnMetadata(
        name="make",
        display_name="Manufacturer",
        description="Vehicle manufacturer or brand.",
        user_intents=[
            "find BMW cars",
            "Toyota SUVs",
            "German brands"
        ],
        synonyms=[
            "make",
            "brand",
            "manufacturer",
            "car brand"
        ],
        related_terms=[
            "luxury brands",
            "reliable brands",
            "performance brands",
            "economy brands"
        ],
        value_type="string",
        example_queries=[
            "black BMW",
            "Toyota hybrid",
            "Audi sedan"
        ],
        sample_size = None
    ),

    "model": ColumnMetadata(
        name="model",
        display_name="Model",
        description="Vehicle model name.",
        user_intents=[
            "looking for a specific model",
        ],
        synonyms=[
            "model",
            "vehicle model"
        ],
        related_terms=[
           "series",
           "trim",
        ],
        value_type="string",
        example_queries=[
            "I want a BMW x5",
            "I am very happy with my old Honda Civic and would like to find something similar",
            "Considering a Ford F-150 or a Chevrolet Silverado"
        ],
        sample_size = None
    ),

    "series": ColumnMetadata(
        name="series",
        display_name="Series",
        description="Manufacturer-specific series or lineup grouping.",
        user_intents=[
            "BMW 3 series",
            "Mercedes C class"
        ],
        synonyms=[
            "series",
            "line",
            "vehicle line"
        ],
        related_terms=[
            "model", 
            "trim"
        ],
        value_type="string",
        example_queries=[
            "bmw 5 series",
            "audi a series", 
            "mercedes c class"
        ],
        sample_size = 5
    ),

    "trim": ColumnMetadata(
        name="trim",
        display_name="Trim",
        description="Specific trim level or configuration package.",
        user_intents=[
            "fully loaded",
            "sport trim",
            "luxury package"
        ],
        synonyms=[
            "trim",
            "variant",
            "package",
            "edition"
        ],
        related_terms=[
            "sport",
            "premium",
            "limited",
            "luxury"
        ],
        value_type="string",
        example_queries=[
            "sport trim suv",
            "premium package"
        ], 
        sample_size = 5
    ),

    "msrp": ColumnMetadata(
        name="msrp",
        display_name="MSRP",
        description="The manufacturer's suggested retail price for the vehicle.",
        user_intents=[
            "find cars under $30,000",
            "compare prices",
            "budget friendly",
            "find cheap cars",
            "good value for money"
        ],
        synonyms=[
            "price",
            "cost",
            "retail price"
        ],
        related_terms=[
            "affordable",
            "expensive",
            "value", 
            "budget",
            "cheap",
        ],
        value_type="float",
        example_queries=[
            "vehicles under 30000 dollars",
            "wont break the bank",
            "affordable suvs",
            "good value car", 
            "my budget is around 25000 dollars"
        ]
    ),

    "body_type": ColumnMetadata(
        name="body_type",
        display_name="Body Type",
        description="Vehicle body style classification.",
        user_intents=[
            "SUV",
            "sedan",
            "wagon",
            "pickup"
        ],
        synonyms=[
            "body type",
            "vehicle type",
            "car type",
            "style"
        ],
        related_terms=[
            "compact", 
            "family",
            "sporty",
            "spacious",
            "practical",
            "offroad"
        ],
        value_type="string",
        example_queries=[
            "two seater sports car",
            "a lot of space for passengers and cargo",
            "car with offroad capability",
            "familiy wagon",
            "fun weekend car"
        ], 
        sample_size = None
    ),

    "doors": ColumnMetadata(
        name="doors",
        display_name="Number of Doors",
        description="Number of vehicle doors.",
        user_intents=[
            "2 door coupe",
            "4 door sedan"
        ],
        synonyms=[
            "doors",
            "door count"
        ],
        related_terms=[
            "compact", 
            "family",
            "sporty",
            "spacious",
            "practical"
        ],
        value_type="integer",
        example_queries=[
            "4 door suv",
            "2 door sports car", 
            "5 door hatchback"
        ], 
        sample_size = None
    ),

    "length_cm": ColumnMetadata(
        name="length_cm",
        display_name="Length",
        description="Vehicle length in centimeters.",
        user_intents=[
            "long car",
            "compact vehicle"
        ],
        synonyms=[
            "length",
            "long",
            "short"
        ],
        related_terms=[
            "fits in parking space",
            "stable",
            "compact",
            "handling", 
            "spacious"
        ],
        units="cm",
        value_type="integer",
        example_queries=[
            "a lot of pasanger space",
            "luxury sedan with large back seats",
            "compact city car", 
            "car that can fit in small parking spaces with less than 450 cm length"
        ]
    ),

    "width_cm": ColumnMetadata(
        name="width_cm",
        display_name="Width",
        description="Vehicle width in centimeters.",
        user_intents=[
            "more isofix points in the back",
            "higher confort in the back",
            "large family car",
        ],
        synonyms=[
            "width",
            "wide",
            "narrow"
        ],
        related_terms=[
            "fits in parking space",
            "stable",
            "compact",
            "good handling", 
            "spacious"
        ],
        units="cm",
        value_type="integer",
        example_queries=[
            "induvidual seats in the back",
            "thee captain chairs in the back",
            "narrow car for city",
            "no more than 180 cm wide for the garage"
        ]
    ),

    "seats": ColumnMetadata(
        name="seats",
        display_name="Seating Capacity",
        description="Number of passenger seats.",
        user_intents=[
            "family car",
            "7 seater",
            "large vehicle"
        ],
        synonyms=[
            "seats",
            "seating",
            "seat count",
            "passenger capacity"
        ],
        related_terms=[
            "5 seater",
            "7 seater",
            "family"
        ],
        value_type="integer",
        example_queries=[
            "7 seat suv",
            "family van", 
            "2 seater sports car", 
            "needs to fit a family of 5 comfortably",
        ], 
        sample_size = None
    ),

    "height_cm": ColumnMetadata(
        name="height_cm",
        display_name="Height",
        description="Vehicle height in centimeters.",
        user_intents=[
            "tall suv",
            "high ceiling cargo van",
            "low profile vehicle"
        ],
        synonyms=[
            "height",
            "tall",
            "low"
        ],
        related_terms=[
            "tall",
            "low"
        ],
        units="cm",
        value_type="integer",
        example_queries=[
            "cargo van with high ceiling",
            "van with standing height",
            "low sports car",
            "needs to fit in the garage with low height clearance",
            "suv with less than 170cm height"
        ]
    ),

    "wheel_base": ColumnMetadata(
        name="wheel_base",
        display_name="Wheelbase",
        description="Distance between front and rear axles in centimeters.",
        user_intents=[
            "stable ride",
            "long wheelbase",
            "short wheelbase", 
            "compact city car", 
        ],
        synonyms=[
            "wheelbase",
            "wheel base",
            "axle distance"
        ],
        related_terms=[
            "long wheelbase",
            "short wheelbase",
            "stable",
            "maneuverable", 
            "nimble",
            "good handling"
        ],
        units="cm",
        value_type="float",
        example_queries=[
            "stable highway ride",
            "long wheelbase luxury sedan",
            "maneuverable compact car",
            "nimble sport car with good handling",
            "large space in the back for passengers and cargo",
            "car with less than 250 cm wheelbase for better handling in the city"
        ]
     ),

     "ground_clearance_cm": ColumnMetadata(
        name="ground_clearance_cm",
        display_name="Ground Clearance",
        description="Distance from ground to lowest vehicle point in centimeters.",
        user_intents=[
            "offroad capability",
            "high ground clearance suv",
            "low clearance sports car"
        ],
        synonyms=[
            "ground clearance",
            "clearance",
            "offroad capability"
        ],
        related_terms=[
            "offroad",
            "high clearance",
            "low clearance",
            "sports car",
            "overland",
            "4x4",
            "four wheel drive"
        ],
        units="cm",
        value_type="float",
        example_queries=[
            "suv with offroad capability",
            "high ground clearance for rough roads",
            "low sports car with good handling", 
            "car with at least 20 cm of ground clearance"
        ]
    ),

    "cargo_capacity": ColumnMetadata(
        name="cargo_capacity",
        display_name="Cargo Capacity",
        description="Standard cargo space in liters.",
        user_intents=[
            "large trunk",
            "cargo van",
            "enough space for luggage",
            "hatchback with enough cargo space",
            "efficient packaging"
        ],
        synonyms=[
            "cargo capacity",
            "trunk space",
            "luggage space"
        ],
        related_terms=[
            "cargo van",
            "large trunk",
            "enough space for luggage"
        ],
        units="liters",
        value_type="integer",
        example_queries=[
            "suv with a lot of space for big family trips",
            "cargo van for moving",
            "sports car with trunk large enough for golf clubs", 
            "at least 500 liters of cargo space"
        ]
    ),

    "curb_weight_kg": ColumnMetadata(
        name="curb_weight_kg",
        display_name="Curb Weight",
        description="Vehicle weight without passengers or cargo in kilograms.",
        user_intents=[
            "lightweight car",
            "heavy duty truck"
        ],
        synonyms=[
            "curb weight",
            "weight"
        ],
        related_terms=[
            "lightweight",
            "heavy", 
            "light",
            "power to weight ratio",
        ],
        units="kg",
        value_type="integer",
        example_queries=[
            "lightweight car for better fuel efficiency",
            "heavy duty truck for towing", 
            "large suv that does not exceed weight limits",
            "sports car with good power to weight ratio",
            "electric family car with less than 2000 kg curb weight"
        ]
    ),

    "max_payload_kg": ColumnMetadata(
        name="max_payload_kg",
        display_name="Max Payload",
        description="Maximum payload capacity in kilograms.",
        user_intents=[
            "high payload capacity",
            "truck for heavy loads"
        ],
        synonyms=[
            "payload",
            "max payload",
            "payload capacity"
        ],
        related_terms=[
            "high payload",
            "truck",
            "heavy loads"
        ],
        units="kg",
        value_type="integer",
        example_queries=[
            "truck with high payload capacity",
            "vehicle for heavy loads",
            "double axle truck", 
            "van that can carry my heavy equipment for work", 
            "suv that can carry a lot of weight in the back"
        ]
    ),

    "max_towing_capacity_kg": ColumnMetadata(
        name="max_towing_capacity_kg",
        display_name="Max Towing Capacity",
        description="Maximum towing capacity in kilograms.",
        user_intents=[
            "high towing capacity",
            "truck for towing"
        ],
        synonyms=[
            "towing capacity",
            "max towing",
            "towing"
        ],
        related_terms=[
            "high towing capacity",
            "truck",
            "towing"
        ],
        units="kg",
        value_type="integer",
        example_queries=[
            "truck with high towing capacity",
            "vehicle for towing",
            "suv that can tow a boat", 
            "something that can pull my 2000 kg camper trailer"
        ]
    ),

    "fuel_type": ColumnMetadata(
        name="fuel_type",
        display_name="Fuel Type",
        description="The type of fuel or powertrain used by the vehicle.",
        user_intents=[
            "electric car",
            "diesel suv",
            "hybrid vehicle",
            "operational cost", 
            "good for city driving", 
            "environmentally friendly"
        ],
        synonyms=[
            "fuel",
            "fuel type",
            "powertrain"
        ],
        related_terms=[
            "gasoline",
            "petrol",
            "gas",
            "diesel",
            "electric",
            "hybrid",
            "plug-in hybrid",
            "PHEV",
            "ev"
        ],
        value_type="string",
        example_queries=[
            "electric suv",
            "diesel bmw",
            "hybrid sedan", 
        ],
        sample_size = None
    ),

    "cylinders": ColumnMetadata(
        name="cylinders",
        display_name="Cylinders",
        description="Number of engine cylinders.",
        user_intents=[
            "v6 engine",
            "v8 muscle car"
        ],
        synonyms=[
            "cylinders",
            "cylinder count"
        ],
        related_terms=[
            "4 cylinders",
            "6 cylinders",
            "8 cylinders",
            "v6",
            "v8",
            "v10", 
            "v12"
            "i6"
        ],
        value_type="integer",
        example_queries=[
            "car with powerful v6 engine",
            "bmw with the inline 6 cylinder engine",
            "v8 sports car",
            "4 cylinder fuel efficient car"
        ],
        sample_size = None
    ),

    "size": ColumnMetadata(
        name="size",
        display_name="Engine Size",
        description="Engine displacement in liters.",
        user_intents=[
            "2.0 liter engine",
            "small engine for better fuel economy", 
            "large displacement for more power",
        ],
        synonyms=[
            "engine size",
            "displacement",
            "liters"
        ],
        related_terms=[
            "2.0L",
            "3.0L",
            "4.0L",
            "small engine",
            "large engine",
            "turbocharged",
            "naturally aspirated"
        ],
        units="liters",
        value_type="float",
        example_queries=[
            "car with 2.0 liter engine",
            "small engine for better fuel economy",
            "turbocharged 4.0L v8",
            "truck with heavy duty diesel engine"
        ]
    ),

    "horsepower_hp": ColumnMetadata(
        name="horsepower_hp",
        display_name="Horsepower",
        description="Engine power output measured in horsepower.",
        user_intents=[
            "fast car",
            "high performance",
            "powerful suv", 
            "good acceleration", 
            "easy highway merging", 
            "dynamic driving experience"
        ],
        synonyms=[
            "horsepower",
            "hp",
            "power"
        ],
        related_terms=[
            "performance",
            "fast",
            "sporty"
        ],
        units="hp",
        value_type="integer",
        example_queries=[
            "300hp suv",
            "fast electric car",
            "high horsepower",
            "powerful sports car with at least 400 hp", 
        ]
    ),

    "torque_nm": ColumnMetadata(
        name="torque_nm",
        display_name="Torque",
        description="Engine torque measured in Newton meters.",
        user_intents=[
            "good towing",
            "strong acceleration"
        ],
        synonyms=[
            "torque",
            "pulling power"
        ],
        related_terms=[
            "acceleration",
            "towing",
            "engine strength", 
            "low end torque"
        ],
        units="Nm",
        value_type="integer",
        example_queries=[
            "high torque diesel",
            "good towing suv",
            "offroad vehicle with strong low end torque",
            "truck with at least 500 Nm of torque"
        ]
    ),

    "drive_type": ColumnMetadata(
        name="drive_type",
        display_name="Drive Type",
        description="Wheel drivetrain configuration.",
        user_intents=[
            "AWD suv",
            "4x4 truck", 
            "offroad capability",
            "good handling in snow"
        ],
        synonyms=[
            "drive type",
            "drivetrain",
            "wheel drive"
        ],
        related_terms=[
            "AWD",
            "FWD",
            "RWD",
            "4WD",
            "all wheel drive",
            "four wheel drive",
            "front wheel drive",
            "rear wheel drive"
        ],
        value_type="string",
        example_queries=[
            "all wheel drive suv",
            "four wheel drive offroad car", 
            "front wheel drive economy car",
            "rear wheel drive sports car", 
            "capable offroad",
            "good for snowy conditions"
        ],
        sample_size = None
    ),

    "transmission": ColumnMetadata(
        name="transmission",
        display_name="Transmission",
        description="Vehicle gearbox or transmission type.",
        user_intents=[
            "automatic car",
            "manual transmission"
        ],
        synonyms=[
            "transmission",
            "gearbox", 
            "speed"
        ],
        related_terms=[
            "automatic",
            "manual",
            "CVT",
            "dual clutch", 
            "6-speed",
        ],
        value_type="string",
        example_queries=[
            "sports car with manual transmission",
            "sports car with dual clutch transmission",
            "automatic suv for easy driving",
            "economy car with cvt transmission"
        ],
        sample_size = None
    ),

    'engine_type': ColumnMetadata(
        name="engine_type",
        display_name="Engine Type",
        description="The type of engine or powertrain configuration.",
        user_intents=[
            "what type of engine does it have",
            "fuel type", 
        ],
        synonyms=[
            "powertrain",
            "motor type",
            "driving power"
        ],
        related_terms=[
            "efficency", 
            "operational cost",
            "environmentally friendly",
            "good for city driving",
            "performance",
            "fuel consumption",
            "electric",
            "hybrid",
            "petrol",
        ],
        value_type="string",
        example_queries=[
            "looking for an electric car",
            "diesel car with good fuel economy",
            "hybrid for city driving on the weekdays and long trips on the weekends",
            "fun gas powered car with good acceleration",
            "I do a lot of highway driving so I would like to have a diesel engine"
        ],
        sample_size = None
    ),

    "fuel_tank_capacity": ColumnMetadata(
        name="fuel_tank_capacity",
        display_name="Fuel Tank Capacity",
        description="Fuel tank capacity in liters.",
        user_intents=[
            "long range",
            "large fuel tank"
        ],
        synonyms=[
            "fuel tank capacity",
            "tank size",
            "fuel capacity"
        ],
        related_terms=[
            "long range",
            "large fuel tank",
            "fuel efficient"
        ],
        units="liters",
        value_type="integer",
        example_queries=[
            "car with long range between fill ups",
            "suv with large fuel tank",
            "diesel car with at least 70 liter fuel tank"
        ]
    ),

    "combined_l_per_100km": ColumnMetadata(
        name="combined_l_per_100km",
        display_name="Fuel Consumption Combined",
        description="Combined fuel consumption in liters per 100 kilometers.",
        user_intents=[
            "fuel efficient",
            "economical car",
            "low consumption"
        ],
        synonyms=[
            "fuel economy",
            "fuel consumption",
            "efficiency",
            "mpg"
        ],
        related_terms=[
            "economical",
            "cheap to run",
            "low fuel usage"
            "ecological"
        ],
        units="L/100km",
        value_type="float",
        example_queries=[
            "fuel efficient hybrid",
            "car with low fuel consumption", 
            "economical car for everyday driving",
            "ecological choice with low emissions",
            "petrol car with less than 7 liters per 100km combined",
            "diesel car with less than 5 liters per 100km combined"
        ]
    ),

    # "epa_city_l_per_100km": ColumnMetadata(
    #     name="epa_city_l_per_100km",
    #     display_name="Fuel Consumption City",
    #     description="City fuel consumption in liters per 100 kilometers.",
    #     user_intents=[
    #         "good for city driving",
    #         "efficient in stop and go traffic"
    #     ],
    #     synonyms=[
    #         "city fuel economy",
    #         "city fuel consumption"
    #     ],
    #     related_terms=[
    #         "city driving",
    #         "stop and go traffic",
    #         "fuel efficient"
    #     ],
    #     units="L/100km",
    #     value_type="float",
    #     example_queries=[
    #         "suv with good city fuel economy",
    #         "car that is efficient in stop and go traffic",
    #         "hybrid with low city consumption",
    #         "efficient car for urban commuting",
    #         "car with low fuel consumption in the city", 
    #         "less than 8 liters per 100km in the city"
    #     ]
    # ),

    # "epa_highway_l_per_100km": ColumnMetadata(
    #     name="epa_highway_l_per_100km",
    #     display_name="Fuel Consumption Highway",
    #     description="Highway fuel consumption in liters per 100 kilometers.",
    #     user_intents=[
    #         "good for highway driving",
    #         "efficient on the highway"
    #     ],
    #     synonyms=[
    #         "highway fuel economy",
    #         "highway fuel consumption"
    #     ],
    #     related_terms=[
    #         "highway driving",
    #         "long distance travel",
    #         "fuel efficient"
    #     ],
    #     units="L/100km",
    #     value_type="float",
    #     example_queries=[
    #         "suv with good highway fuel economy",
    #         "car that is efficient on the highway",
    #         "hybrid with low highway consumption",
    #         "efficient car for long distance travel",
    #         "car with low fuel consumption on the highway",
    #         "less than 6 liters per 100km on the highway"
    #     ]
    # ),

    # "range_city_km": ColumnMetadata(
    #     name="range_city_km",
    #     display_name="City Range",
    #     description="Estimated driving range in city conditions in kilometers.",
    #     user_intents=[
    #         "long city range",
    #         "good for urban driving"
    #     ],
    #     synonyms=[
    #         "city range",
    #         "range in the city"
    #     ],
    #     related_terms=[
    #         "city driving",
    #         "urban range",
    #         "fuel efficient"
    #     ],
    #     units="km",
    #     value_type="integer",
    #     example_queries=[
    #         "suv with long city range",
    #         "car that is good for urban driving",
    #         "wont spend a lot of time at the gas station",
    #         "efficient car for stop and go traffic",
    #         "city car that I can fill up once a month"
    #     ]
    # ),

    "range_highway_km": ColumnMetadata(
        name="range_highway_km",
        display_name="Highway Range",
        description="Estimated driving range in highway conditions in kilometers.",
        user_intents=[
            "long highway range",
            "good for long distance travel"
        ],
        synonyms=[
            "highway range",
            "range on the highway"
        ],
        related_terms=[
            "highway driving",
            "long distance travel",
            "fuel efficient"
        ],
        units="km",
        value_type="integer",
        example_queries=[
            "suv with long highway range",
            "car that is good for long distance travel",
            "wont spend a lot of time at the gas station on road trips",
            "efficient car for highway driving",
            "grand tourer for longer trips"
            "vehicle with good range for long adventures", 
            "at least 600km on the highway between fill ups"
        ]
    ),

    "battery_capacity_electric": ColumnMetadata(
        name="battery_capacity_electric",
        display_name="Battery Capacity",
        description="Battery storage capacity for electric vehicles.",
        user_intents=[
            "large battery",
            "long battery life", 
            "long electric range", 
            "fast charging"
        ],
        synonyms=[
            "battery",
            "battery size",
            "battery capacity"
        ],
        related_terms=[
            "EV",
            "kWh",
            "electric vehicle",
            "long range"
        ],
        units="kWh",
        value_type="float",
        example_queries=[
            "large battery ev",
            "80kwh battery",
            "electric car with long range",
            "quick charging",
            "cheap electric car for short commutes", 
            "electric car with at least 80 kwh battery"
        ]
    ),

    "epa_time_to_charge_hr_240v_electric": ColumnMetadata(
        name="epa_time_to_charge_hr_240v_electric",
        display_name="Time to Charge",
        description="Estimated time to fully charge the battery using a 240V charger in hours.",
        user_intents=[
            "fast charging",
            "quick charge electric car"
        ],
        synonyms=[
            "time to charge",
            "charging time",
            "charge time"
        ],
        related_terms=[
            "fast charging",
            "quick charge",
            "long range"
        ],
        units="hours",
        value_type="float",
        example_queries=[
            "fast charging electric car",
            "ev that can charge quickly on road trips",
            "commuter electric car that I can charge overnight in 6 hours or less"
        ]
    ),

    "epa_kwh_per_100km_electric": ColumnMetadata(
        name="epa_kwh_per_100km_electric",
        display_name="Electric Consumption",
        description="Electric energy consumption in kilowatt-hours per 100 kilometers.",
        user_intents=[
            "efficient electric car",
            "low energy consumption"
        ],
        synonyms=[
            "electric consumption",
            "energy consumption",
            "kWh per 100km"
        ],
        related_terms=[
            "efficient",
            "low energy usage",
            "long range"
        ],
        units="kWh/100km",
        value_type="float",
        example_queries=[
            "efficient electric car with low energy consumption",
            "ev with long range and low kwh per 100km",
            "electric car with energy consumption under 20 kwh per 100km"
        ]
    ),


    "range_electric_km": ColumnMetadata(
        name="range_electric_km",
        display_name="Electric Range",
        description="Maximum electric driving range.",
        user_intents=[
            "long range EV",
            "electric commute"
        ],
        synonyms=[
            "electric range",
            "battery range",
            "ev range"
        ],
        related_terms=[
            "EV",
            "battery life",
            "long range"
        ],
        units="km",
        value_type="integer",
        example_queries=[
            "500km electric range",
            "long range tesla",
            "electric car with enough range for a 60km round trip commute",
            "famility electric car with long range for road trips"
        ]
    ),
}