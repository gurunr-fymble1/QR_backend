from fastapi import FastAPI, Depends, APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
import logging
from datetime import date, datetime
from pydantic import BaseModel
from app.models.database import get_db
from app.models.Booking_msg_model import DailyPass, DailypassDays, Gyms, Gym_Owner, SessionsBookingDays, AllSessions


class StatusUpdate(BaseModel):
    day_id: str
    status: str


app = APIRouter(prefix="/booking-msg")

@app.get("/daily-passes")
async def get_daily_passes(db: AsyncSession = Depends(get_db)):
    try:
        stmt = (
        select(DailyPass, DailypassDays, Gyms, Gym_Owner)
        .join(Gyms, DailyPass.gym_id == Gyms.gym_id)
        .join(Gym_Owner, Gyms.owner_id == Gym_Owner.owner_id)
        .join(
            DailypassDays,
            DailyPass.id == DailypassDays.pass_id
        )
        .where((DailypassDays.scheduled_date >= date.today()) & (DailypassDays.message_status == "Not sent"))
        .order_by(DailypassDays.scheduled_date.desc())
        )

        result = await db.execute(stmt)
        rows = result.all()

        # Group by pass_id and collect dates
        grouped = {}
        for dp, d, g, go in rows:
            if dp.id not in grouped:
                grouped[dp.id] = {
                    "pass": {
                        "id": dp.id,
                        "gym_id": dp.gym_id,
                        "days_total": dp.days_total,
                    },
                    "scheduled_dates": [],
                    "day_ids": [],
                    "owner_contact": go.contact_number if go else None,
                    "gym_name": g.name if g else None,
                    "gym_area": g.area if g else None,
                    "status": d.status if d else None
                }
            if d and d.scheduled_date:
                grouped[dp.id]["scheduled_dates"].append(d.scheduled_date.isoformat())
                grouped[dp.id]["day_ids"].append(d.id)

        # Format as comma-separated
        return [
            {
                **data,
                "scheduled_dates": ", ".join(data["scheduled_dates"]),
                "day_ids": ", ".join(data["day_ids"])
            }
            for data in grouped.values()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch daily passes")


@app.post("/update-message-status/dp")
async def update_message_status(data: StatusUpdate, db: AsyncSession = Depends(get_db)):
    try:
        # Parse comma-separated day_ids and strip whitespace
        day_ids = [d.strip() for d in data.day_id.split(",") if d.strip()]

        stmt = (
            update(DailypassDays)
            .where(DailypassDays.id.in_(day_ids))
            .values(message_status=data.status)
        )
        await db.execute(stmt)
        await db.commit()
        return {"success": True, "message": f"Status updated for {len(day_ids)} records"}
    except Exception as e:
        await db.rollback()
        logging.error(f"Failed to update message status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update status")
    
def format_time(time_str):
    try:
        # Try parsing as HH:MM:SS
        time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
        return time_obj.strftime("%I:%M %p")
    except ValueError:
        # If it fails, return the original string (or handle as needed)
        return time_str
    
@app.get("/sessions")
async def get_sessions(db: AsyncSession = Depends(get_db)):
    try:


        # Now apply date filter
        stmt = (
            select(SessionsBookingDays, Gyms, Gym_Owner, AllSessions)
            .join(Gyms, SessionsBookingDays.gym_id == Gyms.gym_id)
            .join(Gym_Owner, Gyms.owner_id == Gym_Owner.owner_id)
            .join(AllSessions, SessionsBookingDays.session_id == AllSessions.id)
            .where(
                (SessionsBookingDays.booking_date >= date.today()) & (SessionsBookingDays.message_status == "Not sent"),
            )
        )
        result = await db.execute(stmt)
        sessions = result.all()
        print(sessions)

        all_sessions = {}
        for session, g, o, all_sess in sessions:
            # Convert start_time to string in case it's a timedelta
            start_time_str = str(session.start_time) if session.start_time else ""
            formatted_start_time = format_time(start_time_str)

            if session.purchase_id not in all_sessions:
                all_sessions[session.purchase_id] = {
                    "sess":{
                        "id": session.id,
                        "purchase_id": session.purchase_id,
                        "gym_id": session.gym_id,
                        "session_name": all_sess.name if all_sess else None,
                        "scheduled_sessions": [session.booking_date.isoformat() + " " + formatted_start_time],
                        "status": session.status,
                        "message_status": session.message_status,
                    },
                    "gym_name": g.name if g else None,
                    "gym_area": g.area if g else None,
                    "owner_contact": o.contact_number if o else None,
                }
            else:
                all_sessions[session.purchase_id]["sess"]["scheduled_sessions"].append(session.booking_date.isoformat() + " " + formatted_start_time)
        # print(all_sessions)
        return list(all_sessions.values())

    except Exception as e:
        logging.error(f"Failed to fetch sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")

@app.post("/update-message-status/ses")
async def update_message_status(data: StatusUpdate, db: AsyncSession = Depends(get_db)):
    try:
        # Parse comma-separated day_ids and strip whitespace
        id = [d.strip() for d in data.day_id.split(",") if d.strip()]

        stmt = (
            update(SessionsBookingDays)
            .where(SessionsBookingDays.id.in_(id))
            .values(message_status=data.status)
        )
        await db.execute(stmt)
        await db.commit()
        return {"success": True, "message": f"Status updated for {len(id)} records"}
    
    except Exception as e:
        await db.rollback()
        logging.error(f"Failed to update message status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update status")
    