import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Annotated

import requests
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import Settings, Base

SECRET_KEY = "KlgH6AzYDeZeGwD288to79I3vTHT8wp7"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

Base.metadata.create_all(bind=engine)

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="/messaging",
    tags=["messaging"],
)

templates = Jinja2Templates(directory='templates')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/slack_send_message/{message}")
async def slack_send_message(message: str, db: Session = Depends(get_db)):
    settings = db.query(Settings).order_by(Settings.id.desc()).first()

    if settings is not None:
        if settings.slack_webhook_channel is not None:
            url = settings.slack_webhook_channel
            payload = {'text': message}
            response = requests.post(url, json=payload)
            return response.text
        else:
            return "No Slack Webhook URL set"
    
@router.post("/send_email/{message}/{subject}")
async def email_send_message(message: str, subject: str, db: Session = Depends(get_db)):
    settings = db.query(Settings).order_by(Settings.id.desc()).first()

    if settings is not None:
        if settings.email_smtp_server is not None:
            msg = MIMEMultipart()
            msg['From'] = settings.email_smtp_username
            msg['To'] = settings.email_list
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))

            server = smtplib.SMTP(settings.email_smtp_server, settings.email_smtp_port)
            server.starttls()
            server.login(settings.email_smtp_username, settings.email_smtp_password)
            text = msg.as_string()
            server.sendmail(settings.email_smtp_password, settings.email_list, text)
            server.quit()
        else:
            return "No Email SMTP Server set"