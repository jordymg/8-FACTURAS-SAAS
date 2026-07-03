import json
import os
from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials


def _fernet() -> Fernet:
    return Fernet(os.environ["TOKENS_KEY"].encode())


def encrypt_tokens(credentials: Credentials) -> str:
    data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes or []),
    }
    return _fernet().encrypt(json.dumps(data).encode()).decode()


def decrypt_tokens(encrypted: str) -> Credentials:
    data = json.loads(_fernet().decrypt(encrypted.encode()).decode())
    return Credentials(
        token=data["token"],
        refresh_token=data["refresh_token"],
        token_uri=data["token_uri"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        scopes=data["scopes"],
    )
