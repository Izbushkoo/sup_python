import os
import aiohttp
import asyncio

urls = {
    "pgn": "https://b2b.pgn.com.pl/xml?id=26",
    "unimet": "https://img.unimet.pl/cennik.xml",
    "hurtprem": "https://www.hurtowniaprzemyslowa.pl/xml/baselinker.xml",
    "rekman": "https://api.rekman.com.pl/cennik.php?email=aradzevich&password=GeVIOj&TylkoNaStanie=TRUE",
    "growbox": "https://goodlink.pl/xmlapi/1/3/utf8/"
}


async def download_xml(supplier):
    url = urls[supplier]
    file_dest = f'./xml/{supplier}.xml'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response_text = await response.text()

            with open(file_dest, 'w', encoding='utf-8') as file:
                file.write(response_text)
                print(f"File downloaded to {file_dest}")

# Example usage:
# asyncio.run(download_xml('pgn'))
