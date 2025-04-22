# Webservice
# INP21b - Timo Weber & Michael von Ah

################ IMPORTS ################
from fastapi import FastAPI, Depends, HTTPException, Header, Body, Query
from sqlmodel import Session
from dbfunctions import List, Optional, get_db, save_sensor_data, get_client_id_by_name, validate_token_with_access, engine, save_token_to_db, get_recent_sensor_data, get_all_clients
from models import SensorDataIn, SensorData, MessageOnly, User, Client, ClientCreate, TokenResponse, Session as SessionModel
from datetime import datetime, timedelta
from crypto import hash_password, generate_new_token

################ API ################
app = FastAPI(
    title="BBZW-Horizon",
    description="BBZW-Horizon ist ein Tool, welches entwickelt wurde, um durch die Erfassung und Auswertung von Luftqualitätsmesswerten die Luftqualität in den Schulzimmern des BBZW Sursee zu verbessern. Bei dieser API handelt es sich um die Kommunikationsschnittstelle, zwischen den Arduinos, welche mit Sensoren die Daten erfassen und an die API senden. Diese API speichert die Daten dann in der Datenbank, damit diese durch das Frontend abgerufen und visualisiert werden können.",
    summary="Die BBZW-Horizon API dient als Kommunikationsschnittstelle, um Luftqualitätsmesswerte von Arduinos, die mit Sensoren ausgestattet sind, zu erfassen",
    version="0.0.5"
)

# DB Session
def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

def authenticate_user(token: str = Header(...), db: Session = Depends(get_db)):  # Token aus Header
    if not validate_token_with_access(db, token):
        raise HTTPException(status_code=401, detail="Invalid or expired token, or insufficient permissions")

    
@app.post("/sensors/push-data", response_model=MessageOnly, tags=["sensors"])
async def saveNewSensorData(
    client: str,
    data: SensorDataIn,
    db: Session = Depends(get_db),
    auth: bool = Depends(authenticate_user)  # Hier wird das Token durch die Dependency validiert
):
    try:
        # Ermittle die clientid basierend auf dem Client-Namen
        client_id = get_client_id_by_name(db, client)
        if client_id is None:
            raise HTTPException(status_code=404, detail="Client not found")

        # Erstelle ein SensorData-Objekt für die Datenbank
        sensor_data = SensorData(**data.dict())
        sensor_data.clientid = client_id  # Setze die clientid aus der DB

        # Speichern der Sensordaten in der Datenbank
        save_sensor_data(db, sensor_data)

        return MessageOnly(message="Sensor data saved successfully.")
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
    
@app.post("/user/new-session", response_model=TokenResponse, tags=["auth"])
async def generate_token(
    username: str = Body(...),
    password: str = Body(...),
    db: Session = Depends(get_db),
):
    # Überprüfe, ob der Benutzer existiert
    user = db.query(User).filter(User.name == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Überprüfe das Passwort
    if user.password != hash_password(password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    # Erstelle einen neuen Token
    new_token = generate_new_token()  # Generiere den Token
    valid_until = datetime.now() + timedelta(days=30)  # Setze das Datum auf 30 Tage in der Zukunft

    # Speichere den neuen Token in der Datenbank
    new_session = SessionModel(token=new_token, validuntil=valid_until, userid=user.id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    # Rückgabe des Tokens und des Ablaufdatums
    return TokenResponse(token=new_token, validuntil=valid_until)

@app.delete("/user/close-session", response_model=MessageOnly, tags=["auth"])
async def logout_user(token: str = Header(...), db: Session = Depends(get_db)):
    # Überprüfe nur, ob das Token vorhanden ist
    session = db.query(SessionModel).filter(SessionModel.token == token).first()

    # Wenn die Sitzung nicht gefunden wird, ist der Zugriff verweigert
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Lösche die Sitzung
    db.delete(session)
    db.commit()

    return MessageOnly(message="Successfully logged out.")

@app.get("/sensors/get-data", response_model=List[SensorData], tags=["sensors"])
async def get_recent_sensor_data_endpoint(
    client: str,
    token: str = Header(...),  # Token aus dem Header lesen
    start_date: Optional[datetime] = Query(None),  # Optionales Startdatum
    end_date: Optional[datetime] = Query(None),  # Optionales Enddatum
    db: Session = Depends(get_db)
):
    # Authentifiziere den Benutzer
    session = db.query(SessionModel).filter(SessionModel.token == token).first()
    
    # Überprüfe, ob das Token gültig ist
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Ermittle die clientid basierend auf dem Client-Namen
    client_id = get_client_id_by_name(db, client)
    if client_id is None:
        raise HTTPException(status_code=404, detail="Client not found")

    # Setze das end_date auf heute, falls keines übergeben wird
    if end_date is None:
        end_date = datetime.now()

    # Setze das start_date auf 24 Stunden vor dem end_date, falls keines übergeben wird
    if start_date is None:
        start_date = end_date - timedelta(days=1)

    # Hole die Sensordaten im angegebenen Zeitraum
    recent_data = get_recent_sensor_data(db, client_id, start_date, end_date)

    if not recent_data:
        raise HTTPException(status_code=404, detail="No sensor data found in the specified time range.")

    return recent_data  # Rückgabe als JSON

@app.get("/health", response_model=MessageOnly, tags=["health"])
async def health_check():
    """Einfacher Healthcheck-Endpoint, der 'OK' zurückgibt."""
    return MessageOnly(message="OK")

@app.get("/clients/get-client", response_model=List[Client], tags=["clients"])
async def get_clients(
    token: str = Header(...),  # Token aus dem Header lesen
    db: Session = Depends(get_db)
):
    # Authentifiziere den Benutzer
    session = db.query(SessionModel).filter(SessionModel.token == token).first()
    
    # Überprüfe, ob das Token gültig ist
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Hole alle Clients aus der Datenbank
    clients = get_all_clients(db)
    return clients  # Rückgabe als JSON

@app.post("/clients/new-client", response_model=MessageOnly, tags=["clients"])
async def create_client(
    client_create: ClientCreate,
    token: str = Header(...),  # Token aus dem Header lesen
    db: Session = Depends(get_db)
):
    # Authentifiziere den Benutzer
    if not validate_token_with_access(db, token):
        raise HTTPException(status_code=401, detail="Invalid or expired token, or insufficient permissions")

    # Überprüfe, ob der Clientname bereits existiert
    existing_client = db.query(Client).filter(Client.name == client_create.name).first()
    if existing_client:
        raise HTTPException(status_code=400, detail="Client with this name already exists")

    # Erstelle den neuen Client
    new_client = Client(name=client_create.name)
    db.add(new_client)
    db.commit()
    db.refresh(new_client)

    return MessageOnly(message="Client created successfully.")