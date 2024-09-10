from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Configure SQLAlchemy
DATABASE_URL = "sqlite:///user.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Define the User model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hash = Column(String, nullable=False)

    food_counts = relationship("FoodCount", back_populates="user")


# Define the FoodCount model
class FoodCount(Base):
    __tablename__ = "food_count"
    id = Column(Integer, primary_key=True, index=True)
    food_name = Column(String, nullable=False)
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    month = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    hour = Column(Integer, nullable=False)
    minute = Column(Integer, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="food_counts")


def setup_database():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
