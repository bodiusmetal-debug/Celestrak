import os
import json
import requests
from datetime import datetime, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# URL para satélites activos en formato GP JSON
CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json"

def download_and_upload():
    # 1. Definir nombres basados en la hora actual
    now_utc = datetime.now(timezone.utc)
    timestamp_str = now_utc.strftime("%Y%m%d_%H%M%S_UTC")
    filename = f"celestrak_active_{timestamp_str}.json"
    local_path = f"/tmp/{filename}"

    # 2. Descargar los datos de CelesTrak
    print("Descargando datos de CelesTrak...")
    headers = {"User-Agent": "Mozilla/5.0 (DataCapture/1.0)"}
    response = requests.get(CELESTRAK_URL, headers=headers, timeout=60)
    response.raise_for_status()
    
    # Guardado temporal en la máquina virtual de GitHub
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(response.text)

    # 3. Autenticación con Google Drive usando los secretos
    print("Autenticando con Google Drive...")
    creds_json = os.environ.get("GCP_CREDENTIALS")
    folder_id = os.environ.get("DRIVE_FOLDER_ID")
    
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    service = build('drive', 'v3', credentials=creds)

    # 4. Subida del archivo a la carpeta específica
    print(f"Subiendo {filename} a Google Drive...")
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    media = MediaFileUpload(local_path, mimetype='application/json', resumable=True)
    
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    print("¡Archivo subido exitosamente a Drive!")

if __name__ == "__main__":
    download_and_upload()
