# from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine

from typing import AsyncGenerator
from fastapi import Depends
from typing_extensions import Annotated

DATABASE_URL = "mysql+asyncmy://root:tiger@localhost/fittbot_local"

engine = create_async_engine(DATABASE_URL, echo=True)

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

db_session = Annotated[AsyncSession, Depends(get_db)]
