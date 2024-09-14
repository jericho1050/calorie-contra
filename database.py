from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

# Configure SQLAlchemy
DATABASE_URL = "sqlite+aiosqlite:///user.db"
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
Base = declarative_base()

# Define the User model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
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

# Define the Session model
class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True)
    data = Column(Text, nullable=False)
    expiry = Column(Integer, nullable=False)


async def setup_database():
    """Create all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)