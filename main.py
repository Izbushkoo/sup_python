import importlib
import asyncio
from modules.DownloadXML import download_xml
from modules.DatabaseManager import fetch_data_from_db, update_items_by_sku, update_items_by_allegro_id
from modules.ParsingManager import parse_xml_to_json
from modules.DataFiltering.GetAllData import filter_json_object_to_array_of_objects
from modules.DataFiltering.GetAllegroData import filter_supplier_data_for_allegro, filter_supplier_data_for_category, \
    filter_supplier_data_for_category_by_allegro_id
from modules.DataFiltering.GetAmazonData import fetch_and_write_data_for_amazon
from modules.APITokenManager import get_and_check_token
from modules.AlegroApiManager import update_offers, send_telegram_message
from modules.DownloadGrowboxXML import download_growbox_xml

supplier_name = {
    "pgn": "pgn",
    "unimet": "unimet",
    "hurtprem": "hurtprem",
    "rekman": "rekman",
    "growbox": "growbox"
}


async def get_all_data(supplier, is_offers_should_be_updated_on_allegro, multiplier):
    if supplier == 'growbox':
        # await downloadGrowboxXML()
        pass
    else:
        await download_xml(supplier)

    database_items = await fetch_data_from_db(supplier, is_offers_should_be_updated_on_allegro)
    json_from_xml = parse_xml_to_json(supplier)
    filtered_objects = filter_json_object_to_array_of_objects(supplier, json_from_xml, database_items, multiplier)
    return filtered_objects


async def fetch_and_update_allegro(filtered_objects, update_control):
    allegro_objects = filter_supplier_data_for_allegro(filtered_objects)
    token = await get_and_check_token()
    await update_offers(allegro_objects, token, update_control)


# Example usage:
# filtered_objects = await get_all_data(supplier_name['growbox'], True, 1.0)
# await fetch_and_update_allegro(filtered_objects)

async def turn_off_items_by_category(supplier, category):
    filtered_objects = await get_all_data(supplier, True, 1.0)
    items_to_turn_off = filter_supplier_data_for_category_by_allegro_id(filtered_objects, category)
    print(len(items_to_turn_off))
    await update_items_by_allegro_id(supplier, items_to_turn_off)

# Example usage:
# supplier = supplier_name['unimet']
# category = "TECHNIKA MOCOWAŃ"
# await turn_off_items_by_category(supplier, category)
