import os
import asyncio
import aiohttp
import aiofiles
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io


# Путь к файлу учетных данных
SERVICE_ACCOUNT_FILE = 'artful-abode-394612-269fa32007e4.json'


# Авторизовать и создать клиента службы Google Drive
def create_drive_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=credentials)


# Скачать файл из Google Drive
async def download_file(drive, file_id, filename):
    __dirname = os.path.dirname(os.path.abspath(__file__))
    dest_path = os.path.join(__dirname, '../xml', filename)
    print('Destination Path:', dest_path)

    request = drive.files().get_media(fileId=file_id)
    fh = io.FileIO(dest_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Downloaded {int(status.progress() * 100)}%.")


# Перечислить файлы в Google Drive
async def list_files(drive):
    results = drive.files().list(
        q="'1ioZ6c31Dth-l16eLWBJi3zJ6bBkNbUv0' in parents",
        fields="files(id, name)"
    ).execute()
    items = results.get('files', [])
    if not items:
        print('No files found.')
        return []
    else:
        print('Files:')
        download_tasks = []
        for item in items:
            print(f"{item['name']} ({item['id']})")
            download_tasks.append(download_file(drive, item['id'], item['name']))
        return download_tasks


# Скачать XML-файлы Growbox
async def download_growbox_xml():
    try:
        drive = create_drive_service()
        download_tasks = await list_files(drive)
        await asyncio.gather(*download_tasks)
        print('All files downloaded.')
    except Exception as e:
        print(f"An error occurred: {e}")

# Пример использования:
# asyncio.run(download_growbox_xml())
