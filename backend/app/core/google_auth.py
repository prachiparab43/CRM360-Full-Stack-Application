from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException, status
from app.core.config import settings

def verify_google_id_token(token_str: str) -> dict:
    """
    Cryptographically verifies a Google ID token (JWT) using Google public keys.
    Validates signature, issuer, audience, expiration, and ensures email_verified is True.
    Returns verified payload dict with keys: 'sub', 'email', 'name', etc.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Authentication is not configured on the server (missing GOOGLE_CLIENT_ID)."
        )

    try:
        # verify_oauth2_token verifies signature against Google certs, exp, and aud
        request = requests.Request()
        id_info = id_token.verify_oauth2_token(
            token_str, 
            request, 
            settings.GOOGLE_CLIENT_ID
        )

        # Verify issuer
        if id_info.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token issuer."
            )

        # Enforce verified email
        if not id_info.get("email_verified"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account email is not verified."
            )

        return id_info

    except ValueError as e:
        # Token expired, malformed, invalid signature, or aud mismatch
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired Google token: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google token verification failed: {str(e)}"
        )
