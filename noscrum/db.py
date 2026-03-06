from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.orm.session import Session

from noscrum.model import User

engine = create_async_engine("sqlite+aiosqlite:///testing.db")
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def get_session() -> Session:
    async with Session(engine) as session:
        yield session

async def get_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(User, session, User)