from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth as firebase_auth, credentials, initialize_app
import firebase_admin

# Initialize Firebase Admin once
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-adminsdk.json")
    initialize_app(cred)

security = HTTPBearer()

async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        decoded_token = firebase_auth.verify_id_token(credentials.credentials)
        return decoded_token  # contains uid, email, etc.
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")
