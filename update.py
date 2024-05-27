import asyncio
from main import get_all_data, fetch_and_update_allegro
from modules.AlegroApiManager import send_telegram_message

supplier_name = {
    "unimet": "unimet",
    # "growbox": "growbox",
    # "pgn": "pgn",
    # "hurtprem": "hurtprem",
    # "rekman": "rekman"
}


async def update_all_suppliers(update_control, multiplier=0.8):
    for supplier in supplier_name.values():
        print(update_control)
        if update_control['stop']:
            print('Update stopped.')
            await send_telegram_message(f'Updating manually interrupted on {supplier}')
            update_control['stop'] = False
            return

        await send_telegram_message(f'Updating... {supplier}')
        print(supplier)

        filtered_objects = await get_all_data(supplier, True, multiplier)
        await fetch_and_update_allegro(filtered_objects, update_control)
        await send_telegram_message(f'fetchAndUpdateAllegro completed for supplier: {supplier}')


# Пример использования
update_control = {'stop': False}
asyncio.run(update_all_suppliers(update_control, 0.8))
