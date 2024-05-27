import os
import base64
import aiohttp
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env.dev')

access_token = os.getenv('ACCESS_TOKEN')
refresh_token = os.getenv('REFRESH_TOKEN')
uri = os.getenv('MONGO_URI')
db_name = os.getenv('DB_NAME')
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

client = AsyncIOMotorClient(uri)


async def get_token():
    global access_token, refresh_token
    try:
        database = client[db_name]
        collection = database['token']
        document = await collection.find_one({})
        if document:
            access_token = document['access_token']
            refresh_token = document['refresh_token']
    finally:
        client.close()


async def check_token():
    global access_token
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/vnd.allegro.public.v1+json',
    }
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.allegro.pl/me', headers=headers) as res:
            if res.status == 200:
                print('API call successful, token is valid')
                return access_token
            elif res.status == 401:
                print('API call failed, token has expired, refreshing...')
                try:
                    new_access_token = await refresh_access_token()
                    print('Access token refreshed successfully')
                    return new_access_token
                except Exception as err:
                    print('Error refreshing access token:', err)
                    raise
            else:
                print('API call failed, token is invalid:', res.reason)
                raise Exception('Invalid access token')


async def refresh_access_token():
    global access_token, refresh_token
    auth_str = f'{client_id}:{client_secret}'
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    headers = {
        'Authorization': f'Basic {b64_auth_str}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'redirect_uri': 'https://www.fursoller.com/'
    }
    async with aiohttp.ClientSession() as session:
        async with session.post('https://allegro.pl/auth/oauth/token', headers=headers, data=data) as res:
            body = await res.json()
            if res.status == 200:
                access_token = body['access_token']
                refresh_token = body['refresh_token']
                print('Access token refreshed successfully')

                try:
                    database = client[db_name]
                    token_collection = database['token']
                    await token_collection.update_one(
                        {},
                        {'$set': {'access_token': access_token, 'refresh_token': refresh_token}},
                        upsert=True
                    )
                    print('New tokens saved to database successfully')
                except Exception as error:
                    print('Error saving new tokens to database:', error)
                    raise Exception('Failed to save new tokens to database')
                return access_token
            else:
                print(f"Error refreshing access token: {res.status} {res.reason}")
                raise Exception('Failed to refresh access token')


async def get_and_check_token():
    await get_token()
    try:
        checked_access_token = await check_token()
        return checked_access_token
    except Exception as err:
        print('Error checking access token:', err)
        raise

# Example usage:
# access_token = asyncio.run(get_and_check_token())
# print(access_token)
