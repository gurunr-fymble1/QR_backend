from sqlalchemy import Column, String, Integer
from app.models.database import Base

class QRData(Base):
    __tablename__ = "gyms"

    gym_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    area = Column(String(100))
    location = Column(String(200))