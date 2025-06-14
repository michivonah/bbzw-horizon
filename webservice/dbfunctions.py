import os
from sqlmodel import create_engine, Session
from dotenv import load_dotenv
from models import User, SensorData, Client, Session as SessionModel
from datetime import datetime, timedelta
from typing import List, Optional


# Lade Umgebungsvariablen
load_dotenv()
DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING", "postgresql://user:password@localhost/sensordb")

# SQLAlchemy Setup
engine = create_engine(DB_CONNECTION_STRING, echo=True)

def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

# Funktion zum Speichern von Sensordaten
def save_sensor_data(db: Session, sensor_data: SensorData):
    db.add(sensor_data)  # Das Pydantic-Modell kann direkt hinzugefügt werden
    db.commit()
    db.refresh(sensor_data)  # Holt die letzten Informationen des hinzugefügten Eintrags
    return sensor_data

def get_client_id_by_name(db: Session, client_name: str):
    client = db.query(Client).filter(Client.name == client_name).first()
    return client.id if client else None  # Gibt die clientid zurück oder None, wenn nicht gefunden

def validate_token_with_access(db: Session, token: str) -> bool:
    session = db.query(SessionModel).filter(SessionModel.token == token).first()

    # Wenn die Sitzung nicht gefunden wird, ist der Zugriff verweigert
    if not session:
        return False

    # Hole den Benutzer basierend auf userid
    user = db.query(User).filter(User.id == session.userid).first()
    
    # Überprüfe, ob das Token gültig ist und ob api_access True ist
    if session.validuntil <= datetime.now().date() or not user.api_access:
        return False

    return True  # Token ist gültig und User hat API-Zugriff

def check_api_access(db: Session, token: str) -> bool:
    session = db.query(SessionModel).filter(SessionModel.token == token).first()

    # Wenn die Sitzung nicht gefunden wird, ist der Zugriff verweigert
    if not session:
        return False

    # Hole den Benutzer basierend auf userid
    user = db.query(User).filter(User.id == session.userid).first()

    # Überprüfe, ob api_access True ist
    return user.api_access if user else False  # Gibt True oder False zurück

def save_token_to_db(db: Session, token: str, user_id: int, valid_until: datetime):
    new_session = SessionModel(token=token, validuntil=valid_until, userid=user_id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

def get_recent_sensor_data(db: Session, client_id: int, start_date: datetime, end_date: datetime) -> List[SensorData]:
    return db.query(SensorData).filter(
        SensorData.timestamp >= start_date,
        SensorData.timestamp < end_date,  # Das end_date sollte exklusiv sein
        SensorData.clientid == client_id
    ).all()

def get_all_clients(db: Session) -> List[Client]:
    return db.query(Client).all()