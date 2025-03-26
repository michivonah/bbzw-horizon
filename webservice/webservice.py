# Webservice
# INP21b - Timo Weber & Michael von Ah

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import dbfunctions as db
import requests, secrets, hashlib, re, string, random, os
from datetime import datetime, timedelta, date, time
import json
from datetime import datetime

DATABASE_URL = os.getenv("DB_CONNECTION_STRING", "postgresql://user:password@localhost/sensordb")

""" class apiFunctions:
    def __init__(self) -> None:
        self.alternativeImage = "https://cdn.ep.neodym.dev/media/20240505-halloween.jpeg"

    def getAttractionList(self):
        query = 'SELECT "name", "id", "imageurl", "description" FROM "attraction" ORDER BY "name";'
        attractions = db.executeQuery(query)
        if attractions:
            return attractions
        else:
            raise Exception("Cannot generate list of attractions. Request invalid") """
        

#### API ####
app = FastAPI(
    title="M241-M245-BBZW-Horizion",
    description="BBZW-Horizon",
    summary="BBZW-Horizon",
    version="0.0.1"
)

class Session(BaseModel):
    username: str = None
    token: str = None
    message: str = None
    timestamp: datetime = datetime.now()

@app.post("/account/new-session", tags=["account"])
async def initNewSessionApi(username: str, password: str) -> Session:
    try:
        return Session(username="username", token="sessionToken", message="Session initiated successfully")
    except Exception as error:
        raise HTTPException(status_code=401, detail=f"{error}")