from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import Column, Integer, Float, String, DateTime, create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DB_CONNECTION_STRING", "postgresql://user:password@localhost/sensordb")

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()

# Neue Clients-Tabelle
class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    clientid = Column(Integer, ForeignKey("clients.id"), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    temperature = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    voc = Column(Float)
    gas = Column(Float)

    client = relationship("Client")

class SessionToken(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    validuntil = Column(DateTime)
    userid = Column(Integer, ForeignKey("user.id"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_token(token: str, db: Session):
    session = db.query(SessionToken).filter(SessionToken.token == token).first()
    if not session or session.validuntil < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return session

@app.post("/sensor-data/")
def receive_sensor_data(
    token: str,
    clientname: str,  # Ändert clientid zu clientname
    temperature: float,
    humidity: float,
    pressure: float,
    voc: float,
    gas: float,
    db: Session = Depends(get_db)
):
    verify_token(token, db)

    # Suche die Client-ID anhand des Client-Namens
    client = db.query(Client).filter(Client.name == clientname).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    sensor_data = SensorData(
        clientid=client.id,  # Verwende die gefundene ID
        temperature=temperature,
        humidity=humidity,
        pressure=pressure,
        voc=voc,
        gas=gas
    )
    db.add(sensor_data)
    db.commit()
    db.refresh(sensor_data)
    return {"message": "Data received", "id": sensor_data.id}

@app.get("/sensor-data/")
def get_sensor_data(db: Session = Depends(get_db)):
    data = db.query(SensorData).all()
    return data

# Erstelle die Tabellen, falls sie noch nicht existieren
Base.metadata.create_all(bind=engine)
