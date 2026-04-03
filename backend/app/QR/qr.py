from fastapi import FastAPI, Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import logging
from app.models.database import get_db
from app.models.qr_model import QRData
from urllib.parse import unquote

from base64 import b64encode, b64decode
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

AES_KEY = "a3f71e45f914e539f2ff5bca397ce292"
AES_KEY=AES_KEY.encode()


BLOCK_SIZE = 128 

app = APIRouter(prefix="/qr")

    
def decrypt_gym_id(encrypted_str: str) -> int:
    try:
        iv, ct = encrypted_str.split(":")
        iv = b64decode(iv + "==")
        ct = b64decode(ct + "==")
        cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded = decryptor.update(ct) + decryptor.finalize()
        unpadder = PKCS7(BLOCK_SIZE).unpadder()
        pt = unpadder.update(padded) + unpadder.finalize()
        return int(pt.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"Invalid gym_id decryption: {str(e)}")

@app.get("/scan/{qr_id:path}")
async def get_qr_value(qr_id: str, db: AsyncSession = Depends(get_db)):
    try:
        qr_id = unquote(qr_id) 
        gym_id = decrypt_gym_id(qr_id)

        stmt = select(QRData).where(QRData.gym_id == gym_id)
        result = await db.execute(stmt)
        data = result.scalar_one_or_none()

        if not data:
            return {"message": "Invalid QR"}

        # ensure this gym_id is recorded in qr_status.qr_generated_gyms if not present
        logger = logging.getLogger(__name__)
        try:
            # Atomic insert: insert row only if gym_id does not already exist
            insert_sql = text("""
                INSERT INTO qr_status.qr_generated_gyms (gym_id, name, area, location)
                SELECT :gym_id, :name, :area, :location
                FROM DUAL
                WHERE NOT EXISTS (
                    SELECT 1 FROM qr_status.qr_generated_gyms WHERE gym_id = :gym_id
                )
            """)
            await db.execute(insert_sql, {
                "gym_id": gym_id,
                "name": data.name or "",
                "area": data.area or "",
                "location": data.location or ""
            })
            await db.commit()
        except Exception as e:
            logger.exception("Failed inserting into qr_status.qr_generated_gyms")

        return {
            "id": data.gym_id,
            "name": data.name,
            "area": data.area,
            "location": data.location
        }
    except ValueError as ve:
        return {"message": str(ve)}