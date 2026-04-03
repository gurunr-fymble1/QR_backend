from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.QR import qr, booking_msg
from app.models.database import engine

# from app.telecaller.init_model import init_models

app = FastAPI()

# @app.on_event("startup")
# async def on_startup():
#     await init_models()

origins = [
	"http://localhost:5173",
	"http://localhost:5174",
]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(qr.app)
app.include_router(booking_msg.app)