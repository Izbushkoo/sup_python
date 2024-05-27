import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env.dev')

supplier_database_id = {
    "pgn": "63d41080b4d9fc9a7f1aeb25",
    "unimet": "63d4110fb4d9fc9a7f1aeb28",
    "hurtprem": "63d39858b4d9fc9a7f1acedb",
    "rekman": "6400778b7b4bb4cab20ccccf",
    "growbox": "640f0ddec6defcd7745fe210"
}

uri = os.getenv('MONGO_URI')
db_name = os.getenv('DB_NAME')
db_collection = os.getenv('DB_COLL')


async def fetch_data_from_db(supplier, allegro_update):
    supplier_id = supplier_database_id[supplier]
    client = AsyncIOMotorClient(uri)

    try:
        database = client[db_name]
        collection = database[db_collection]

        query = {
            "groups": supplier_id,
            "allegro_we_sell_it": allegro_update
        }
        options = {
            "projection": {"_id": 0, "allegro_oferta_id": 1, "supplier_sku": 1}
        }
        documents = collection.find(query, options)

        items_array = await documents.to_list(length=None)
        return items_array
    finally:
        client.close()


async def update_items_by_sku(supplier, skus):
    if not supplier or not skus or len(skus) == 0:
        print("Supplier or SKUs not provided")
        return

    supplier_id = supplier_database_id[supplier]
    client = AsyncIOMotorClient(uri)

    cleaned_skus = [sku.split("_", 2)[-1] for sku in skus]

    try:
        database = client[db_name]
        collection = database[db_collection]

        filter_ = {
            "groups": supplier_id,
            "supplier_sku": {"$in": cleaned_skus}
        }

        update = {
            "$set": {"allegro_we_update_it": False}
        }

        result = await collection.update_many(filter_, update)
        print(f"{result.modified_count} document(s) was/were updated.")
    except Exception as error:
        print("Error updating documents:", error)
    finally:
        client.close()


async def update_items_by_allegro_id(supplier, allegro_ids):
    if not supplier or not allegro_ids or len(allegro_ids) == 0:
        print("Supplier or IDs not provided")
        return

    supplier_id = supplier_database_id[supplier]
    client = AsyncIOMotorClient(uri)

    try:
        database = client[db_name]
        collection = database[db_collection]

        filter_ = {
            "groups": supplier_id,
            "allegro_oferta_id": {"$in": allegro_ids}
        }
        print(filter_)
        update = {
            "$set": {"allegro_we_update_it": False}
        }
        result = await collection.update_many(filter_, update)
        print(result)
        print(f"{result.modified_count} document(s) was/were updated.")
    except Exception as error:
        print("Error updating documents:", error)
    finally:
        client.close()

# Пример вызова асинхронной функции
# asyncio.run(fetch_data_from_db("unimet", True))
# asyncio.run(update_items_by_sku("unimet", ["UNIMET_12345", "UNIMET_67890"]))
# asyncio.run(update_items_by_allegro_id("unimet", ["12345", "67890"]))
