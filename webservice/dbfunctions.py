import os
from sqlmodel import create_engine, Session
from dotenv import load_dotenv
from models import SensorData, Client

# Lade Umgebungsvariablen
load_dotenv()
DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING", "postgresql://user:password@localhost/sensordb")

# SQLAlchemy Setup
engine = create_engine(DB_CONNECTION_STRING, echo=True)

# Funktion zum Speichern von Sensordaten
def save_sensor_data(db: Session, sensor_data: SensorData):
    db.add(sensor_data)  # Das Pydantic-Modell kann direkt hinzugefügt werden
    db.commit()
    db.refresh(sensor_data)  # Holt die letzten Informationen des hinzugefügten Eintrags
    return sensor_data

# dbfunctions.py
def get_client_id_by_name(db: Session, client_name: str):
    client = db.query(Client).filter(Client.name == client_name).first()
    return client.id if client else None  # Gibt die clientid zurück oder None, wenn nicht gefunden