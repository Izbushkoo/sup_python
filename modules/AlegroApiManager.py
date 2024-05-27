import json
import uuid
import math
import asyncio
import re
import requests
import os

# Загрузка переменных окружения
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env.dev')


async def send_telegram_message(message):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}"

    try:
        response = requests.get(url)
        json_response = response.json()
        if json_response['ok']:
            print(f"Telegram message sent successfully: {message}")
        else:
            print(f"Error sending Telegram message: {json_response['description']}")
    except Exception as error:
        print(f"Error sending Telegram message: {error}")


async def update_offers(offers_array, access_token, update_control):
    try:
        array_with_price_errors_to_update = []
        array_to_end = []
        array_to_activate = []
        failed_http_request = []

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/vnd.allegro.public.v1+json",
            "Accept": "application/vnd.allegro.public.v1+json",
        }

        max_retries = 5

        for offer in offers_array:
            id = offer.get('id')
            stock = offer.get('stock')
            price = offer.get('price')

            if stock == 0:
                print(f"Offer {id} is 0 stock. Pushed to the arrayToEnd.")
                array_to_end.append(offer)
                continue

            if update_control.get('stop'):
                print('Update stopped.')
                await send_telegram_message('Update stopped')
                return

            data = {
                "sellingMode": {
                    "price": {
                        "amount": price,
                        "currency": "PLN",
                    },
                },
                "stock": {
                    "available": stock,
                    "unit": "UNIT",
                },
            }

            url = f"https://api.allegro.pl/sale/product-offers/{id}"
            retries = 0
            success = False

            while retries < max_retries and not success:
                try:
                    response = requests.patch(url, headers=headers, json=data)
                    if response.status_code in [200, 202]:
                        print(f"Offer {id} updated successfully")
                        array_to_activate.append(offer)
                        success = True
                    else:
                        handle_errors(response, offer, array_to_end, array_with_price_errors_to_update)
                        success = True
                except requests.HTTPError as http_err:
                    print(f"HTTP error occurred: {http_err}")
                    status_code = http_err.response.status_code if http_err.response else None
                    if status_code in [500, 501, 502, 503, 504] or http_err.errno in ["ECONNRESET", "ETIMEDOUT"]:
                        print("Bad request - will try again in 5 seconds...")
                        retries += 1
                        await sleep(5)
                    else:
                        handle_errors(http_err.response, offer, array_to_end, array_with_price_errors_to_update)
                        retries = max_retries
                        success = True

            if not success:
                print(f"I failed to update {id}")
                failed_http_request.append(offer)

            print("activate:", len(array_to_activate))
            print("end:", len(array_to_end))
            print("updatePriceErrors", len(array_with_price_errors_to_update))

        if array_with_price_errors_to_update:
            print(f"Updating {len(array_with_price_errors_to_update)} offers with price error...")
            await update_offers(array_with_price_errors_to_update, access_token, update_control)
        if array_to_activate:
            print(f"Activating {len(array_to_activate)} offers...")
            await update_offers_status(access_token, array_to_activate, "ACTIVATE")
        if array_to_end:
            print(f"Finishing {len(array_to_end)} offers with errors...")
            await update_offers_status(access_token, array_to_end, "END")

        print("Here are the items that could not be updated due to a server error:", failed_http_request)

    except Exception as error:
        print(f"Critical error: {error}")
        await send_telegram_message(f"Critical error in update_offers function: {error}")
        raise error


def handle_errors(response, offer, array_to_end, array_with_price_errors_to_update):
    try:
        json_response = response.json()
    except json.JSONDecodeError:
        print("Unknown error: empty error object")
        return

    status_code = response.status_code
    error_object = json_response['errors'][0] if json_response.get('errors') else None
    error_for_id = {
        "id": offer.get('id'),
        "errorCode": error_object.get('code'),
        "errorText": error_object.get('userMessage'),
    }

    if error_object:
        if status_code == 400 and error_object.get('code') == "IllegalOfferUpdateException.IllegalIncreasePrice":
            error_text = error_object.get('userMessage')
            regex_match = re.search(r'([0-9]+,[0-9]+) PLN', error_text)
            if regex_match:
                price_string = regex_match.group(1)
                price = math.floor(float(price_string.replace(',', '.')))
                new_price = price - 0.01
                array_with_price_errors_to_update.append(
                    {"id": offer.get('id'), "price": new_price, "stock": offer.get('stock')})
        elif status_code in [401, 403]:
            print(f"Error code {status_code}: {error_object.get('userMessage')}")
        elif status_code == 422 and error_object.get('code') == "IllegalOfferUpdateException.IllegalIncreasePrice":
            error_text = error_object.get('userMessage')
            regex_match = re.search(r'([0-9]+,[0-9]+) PLN', error_text)
            if regex_match:
                price_string = regex_match.group(1)
                price = math.floor(float(price_string.replace(',', '.')))
                new_price = price - 0.01
                array_with_price_errors_to_update.append(
                    {"id": offer.get('id'), "price": new_price, "stock": offer.get('stock')})
                print(f"New price for {offer.get('id')} is {new_price}.")
            else:
                print("Failed to parse the price!")
        else:
            print(f"Offer {offer.get('id')} got an error code {status_code}: {error_object.get('userMessage')}")
            array_to_end.append(error_for_id)
    else:
        print(f"Error status code: {status_code}. Error: {error_object}")
        array_to_end.append(error_for_id)


async def update_offers_status(access_token, offers, action):
    batch_size = 1000
    max_offers_per_minute = 9000
    start_index = 0

    while start_index < len(offers):
        end_index = min(start_index + batch_size, len(offers))
        batch_offers = offers[start_index:end_index]

        payload = {
            "offerCriteria": [
                {
                    "offers": [{"id": offer.get('id')} for offer in batch_offers],
                    "type": "CONTAINS_OFFERS",
                }
            ],
            "publication": {
                "action": action,
            },
        }

        command_id = str(uuid.uuid4())
        url = f"https://api.allegro.pl/sale/offer-publication-commands/{command_id}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/vnd.allegro.public.v1+json',
            'Content-Type': 'application/vnd.allegro.public.v1+json'
        }

        try:
            response = requests.put(url, headers=headers, json=payload)
            if response.status_code == 201:
                print(f"Command {action}ed successfully. Command ID: {command_id}. {response.text}")
            else:
                print(f"Error {response.status_code}: {response.text}")
        except Exception as error:
            print(f"Error sending request: {error}")

        start_index += batch_size

        if start_index % max_offers_per_minute == 0:
            print("Waiting for 1 minute before processing more offers...")
            await sleep(60000)
        else:
            await sleep(500)


def sleep(ms):
    return asyncio.sleep(ms / 1000)
