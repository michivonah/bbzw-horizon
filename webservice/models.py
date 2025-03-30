from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from sqlmodel import SQLModel, Field

class MessageOnly(BaseModel):
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)

class TokenResponse(BaseModel):
    token: str
    validuntil: datetime

class User(SQLModel, table=True):
    __tablename__ = "user"
    id: int = Field(default=None, primary_key=True)
    name: str = Field(max_length=50)
    mail: str = Field(max_length=150)
    password: str = Field(max_length=250)
    api_access: bool = Field(default=False)

class Session(SQLModel, table=True):
    __tablename__ = "sessions"
    id: int = Field(default=None, primary_key=True)
    token: str = Field(max_length=96)
    validuntil: datetime  # Verwende datetime hier
    userid: int = Field(foreign_key="user.id")  # Foreign Key auf User

class Client(SQLModel, table=True):
    __tablename__ = "clients"  # Definiere den Tabellennamen für Clients
    id: int = Field(default=None, primary_key=True)
    name: str = Field(max_length=50)  # Stelle sicher, dass der Name der DB-Struktur entspricht

class SensorDataIn(BaseModel):  # Klasse für den Input (d.h., die API-Dokumentation)
    timestamp: datetime = Field(default_factory=datetime.now)
    temperature: float = Field(default=None, nullable=True)
    humidity: float = Field(default=None, nullable=True)
    pressure: float = Field(default=None, nullable=True)
    voc: float = Field(default=None, nullable=True)
    gas: float = Field(default=None, nullable=True)


class SensorData(SQLModel, table=True):
    __tablename__ = "sensor_data"
    id: int = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    temperature: float = Field(default=None, nullable=True)
    humidity: float = Field(default=None, nullable=True)
    pressure: float = Field(default=None, nullable=True)
    voc: float = Field(default=None, nullable=True)
    gas: float = Field(default=None, nullable=True)
    clientid: int = Field(default=None, nullable=True)