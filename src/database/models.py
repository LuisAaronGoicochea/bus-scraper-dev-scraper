from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Enum, Boolean, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum

Base = declarative_base()

# Define Enums
class AirConditioningOptions(enum.Enum):
    REAR = "REAR"
    DASH = "DASH"
    BOTH = "BOTH"
    OTHER = "OTHER"
    NONE = "NONE"

class USRegion(enum.Enum):
    NORTHEAST = "NORTHEAST"
    MIDWEST = "MIDWEST"
    WEST = "WEST"
    SOUTHWEST = "SOUTHWEST"
    SOUTHEAST = "SOUTHEAST"
    OTHER = "OTHER"

# Define tables
class Bus(Base):
    __tablename__ = 'buses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(256), nullable=False)  # `nullable=False` asegura que no haya títulos vacíos
    year = Column(String(10), nullable=True)
    make = Column(String(25), nullable=True)
    model = Column(String(50), nullable=True)
    body = Column(String(25), nullable=True)
    chassis = Column(String(25), nullable=True)
    engine = Column(String(60), nullable=True)
    transmission = Column(String(60), nullable=True)
    mileage = Column(String(100), nullable=True)
    passengers = Column(String(60), nullable=True)
    wheelchair = Column(String(60), nullable=True)
    color = Column(String(60), nullable=True)
    interior_color = Column(String(60), nullable=True)
    exterior_color = Column(String(60), nullable=True)
    published = Column(Boolean, default=False, nullable=False)
    featured = Column(Boolean, default=False, nullable=False)
    sold = Column(Boolean, default=False, nullable=False)
    scraped = Column(Boolean, default=False, nullable=False)
    draft = Column(Boolean, default=False, nullable=False)
    source = Column(String(300), nullable=True)
    source_url = Column(String(1000), nullable=True, unique=True)
    price = Column(String(30), nullable=True)
    cprice = Column(String(30), nullable=True)
    vin = Column(String(60), nullable=True)
    updated_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, nullable=True)
    gvwr = Column(String(50), nullable=True)
    dimensions = Column(String(300), nullable=True)
    luggage = Column(Boolean, default=False, nullable=False)
    state_bus_standard = Column(String(25), nullable=True)
    airconditioning = Column(Enum(AirConditioningOptions), default=AirConditioningOptions.NONE, nullable=False)
    location = Column(String(30), nullable=True)
    brake = Column(String(30), nullable=True)
    contact_email = Column(String(100), nullable=True)
    contact_phone = Column(String(100), nullable=True)
    us_region = Column(Enum(USRegion), default=USRegion.OTHER, nullable=False)
    description = Column(Text, nullable=True)
    score = Column(Boolean, default=False, nullable=False)
    category_id = Column(Integer, default=0, nullable=False)

    overview = relationship("BusOverview", back_populates="bus", cascade="all, delete-orphan")
    images = relationship("BusImage", back_populates="bus", cascade="all, delete-orphan")

class BusOverview(Base):
    __tablename__ = 'buses_overview'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bus_id = Column(Integer, ForeignKey('buses.id'), nullable=False)
    mdesc = Column(Text, nullable=True)
    intdesc = Column(Text, nullable=True)
    extdesc = Column(Text, nullable=True)
    features = Column(Text, nullable=True)
    specs = Column(Text, nullable=True)

    bus = relationship("Bus", back_populates="overview")

class BusImage(Base):
    __tablename__ = 'buses_images'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=True)
    url = Column(String(1000), nullable=True)
    description = Column(Text, nullable=True)
    image_index = Column(Integer, default=0)
    bus_id = Column(Integer, ForeignKey('buses.id'), nullable=False)

    bus = relationship("Bus", back_populates="images")

# Database setup
def get_database_session(connection_string):
    engine = create_engine(connection_string, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
