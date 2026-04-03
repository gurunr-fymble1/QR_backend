from sqlalchemy import Column, String, Integer, Date, ForeignKey, JSON
from app.models.database import Base
from sqlalchemy.orm import relationship

class DailyPass(Base):
    __tablename__ = "daily_passes"
    __table_args__ = {"schema": "dailypass"}

    id = Column(String(36), primary_key=True, index=True)
    gym_id = Column(Integer)
    days_total = Column(Integer)

    days = relationship("DailypassDays", back_populates="pass_obj")


class DailypassDays(Base):
    __tablename__ = "daily_pass_days"
    __table_args__ = {"schema": "dailypass"}

    id = Column(String(36), primary_key=True, index=True)
    pass_id = Column(String(36), ForeignKey("dailypass.daily_passes.id"))
    scheduled_date = Column(Date)
    status = Column(String(20))
    message_status = Column(String(20))

    pass_obj = relationship("DailyPass", back_populates="days")

class Gyms(Base):
    __tablename__ = "gyms"
    __table_args__ = {"schema": "fittbot_local"}

    gym_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    owner_id = Column(Integer)
    area = Column(String(100))

class Gym_Owner(Base):
    __tablename__ = "gym_owners"
    __table_args__ = {"schema": "fittbot_local"}

    owner_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    contact_number = Column(String(100))

class SessionsBookingDays(Base):
    __tablename__ = "session_booking_days"
    __table_args__ = {"schema": "sessions"}

    id = Column(String(36), primary_key=True, index=True)
    purchase_id = Column(String(36))
    gym_id = Column(Integer)
    session_id = Column(Integer)
    booking_date = Column(Date)
    start_time = Column(String(20))
    status = Column(String(20))
    message_status = Column(String(20))

class AllSessions(Base):
    __tablename__ = "all_sessions"
    __table_args__ = {"schema": "sessions"}

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100))