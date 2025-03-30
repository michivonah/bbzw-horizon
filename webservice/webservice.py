# Webservice
# INP21b - Timo Weber & Michael von Ah

################ IMPORTS ################
from fastapi import FastAPI, Depends, HTTPException, Header, Body
from sqlmodel import Session
from dbfunctions import save_sensor_data, get_client_id_by_name, validate_token_with_access, engine, save_token_to_db
from models import SensorDataIn, SensorData, MessageOnly, User, TokenResponse, Session as SessionModel
from datetime import datetime, timedelta
from crypto import hash_password, generate_new_token
 

################ API ################
app = FastAPI(
    title="BBZW-Horizon",
    description="BBZW-Horizon",
    summary="BBZW-Horizon",
    version="0.0.2"
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