import io

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


def _service(credentials: Credentials):
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def create_invoice_folder(credentials: Credentials, email: str) -> str:
    service = _service(credentials)
    folder = service.files().create(
        body={
            "name": f"Facturas — {email}",
            "mimeType": "application/vnd.google-apps.folder",
        },
        fields="id",
    ).execute()
    return folder["id"]


def upload_image(
    credentials: Credentials,
    folder_id: str,
    filename: str,
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
) -> str:
    service = _service(credentials)
    media = MediaIoBaseUpload(io.BytesIO(image_bytes), mimetype=mime_type)
    file = service.files().create(
        body={"name": filename, "parents": [folder_id]},
        media_body=media,
        fields="id,webViewLink",
    ).execute()
    return file["webViewLink"]
