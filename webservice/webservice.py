# Webservice
# INP21b - Timo Weber & Michael von Ah

################ IMPORTS ################
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session
from dbfunctions import save_sensor_data, get_client_id_by_name, engine
from models import SensorDataIn, SensorData, MessageOnly 
 

################ API ################
app = FastAPI(
    title="M241-M245-BBZW-Horizon",
    description="BBZW-Horizon",
    summary="BBZW-Horizon",
    version="0.0.1"
)

# DB Session
def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

# class Session(BaseModel):
#     username: str = None
#     token: str = None
#     message: str = None
#     timestamp: datetime = datetime.now()




# @app.post("/account/new-session", tags=["account"])
# async def initNewSessionApi(username: str, password: str) -> Session:
#     try:
#         return Session(username="username", token="sessionToken", message="Session initiated successfully")
#     except Exception as error:
#         raise HTTPException(status_code=401, detail=f"{error}")
    
@app.post("/sensors/push-data", response_model=MessageOnly, tags=["sensors"])
async def saveNewSensorData(token: str, client: str, data: SensorDataIn, db: Session = Depends(get_db)):
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