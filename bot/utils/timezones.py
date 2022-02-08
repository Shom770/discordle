from asyncio import to_thread

import aiohttp
from timezonefinder import TimezoneFinder

from errors import CityNotFoundError

timezone_finder = TimezoneFinder()


async def get_timezone(city_name: str):
    """Get"""
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(
                f"https://nominatim.openstreetmap.org/search.php?q={city_name}&format=json",
                ssl=False
        ) as response:
            response = await response.json()
            if not response:
                raise CityNotFoundError(city_name)
            else:
                latitude, longitude = float(response[0]["lat"]), float(response[0]["lon"])

    return await to_thread(timezone_finder.timezone_at, lat=latitude, lng=longitude)
