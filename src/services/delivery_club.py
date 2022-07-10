import json
import time
import asyncio
import aiohttp
import requests
import urllib.parse

from typing import Any, Iterable, NamedTuple
from bs4 import BeautifulSoup


class Notifier:
    def __init__(self) -> None:
        self.token = "5499393500:AAETLacc9Xcfk2h5m0TMCeuBD5__clJz4v4"
        self.chat_id = -639281506

    def send_message(self, message: str) -> None:
        message = urllib.parse.quote(message)

        requests.get(f"https://api.telegram.org/bot{self.token}/sendMessage?chat_id={self.chat_id}&parse_mode=html&text={message}")


class City(NamedTuple):
    id: str
    name: str
    latitude: float
    longitude: float


class Restaurant(NamedTuple):
    name: str
    slug: str


class Product(NamedTuple):
    id: int
    name: str
    description: str
    price: float
    image: str
    weight: str


class Parser:
    BASE_URL: str = "https://www.delivery-club.ru"


    def __init__(self, limit: asyncio.Semaphore, rate: float) -> None:
        self.limit = limit
        self.rate = rate
        self.session = aiohttp.ClientSession()

        self.notifier = Notifier()

    async def __aenter__(self):
        self.notifier.send_message("Parsing...")

        return self

    async def __aexit__(self, *excinfo):
        self.notifier.send_message("Finished")

        await self.session.close()

    async def get_cities(self, city_names: Iterable[str] = []) -> list[City]:
        initial_state = await self.__get_initial_state(Parser.BASE_URL)
        city_items = initial_state["cities"]["items"]

        if city_names:
            city_items = filter(lambda ci: ci["name"] in city_names, city_items)

        cities: list[City] = []

        for city_item in city_items:
            city = City(
                city_item["cityId"],
                city_item["name"],
                city_item["latitude"],
                city_item["longitude"],
            )

            cities.append(city)

        self.notifier.send_message(f"Found cities: {len(cities)}")

        return cities
    
    async def get_restaurants(self, city: City) -> list[Restaurant]:
        limit = 200
        offset = 0
        has_more = True

        restaurants: list[Restaurant] = []

        while has_more:
            async with self.session.get("https://api.delivery-club.ru/api1.3/screen/web/components", params={
                "limit": limit,
                "offset": offset,
                "latitude": city.latitude,
                "longitude": city.longitude,
                "fastFilters": "group",
                "cityId": city.id,
                "cacheBreaker": int(time.time()),
            }, ssl=False) as response:

                data = await response.json()

                components = data["components"]
                offset = data["offset"]
                has_more = data.get("hasMore", False)
                
                for component in components:
                    restaurant = Restaurant(
                        component["vendor"]["name"],
                        component["vendor"]["chain"]["alias"],
                    )

                    restaurants.append(restaurant)

                # time.sleep(1)

        self.notifier.send_message(f"Found restaurants in {city.name}: {len(restaurants)}")

        return restaurants

    async def get_products(self, restaurant: Restaurant) -> list[Product]:
        initial_state = await self.__get_initial_state(f"{Parser.BASE_URL}/srv/{restaurant.slug}")
        products: list[Product] = []

        items = initial_state["vendor"]["products"]

        for item in items:
            if item["price"]["currency"] != "RUB":
                continue

            product = Product(
                int(item["id"]["primary"]),
                item["name"],
                item["description"],
                float(item["price"]["value"]),
                item["images"]["650"],
                item["properties"]["weight"],
            )

            products.append(product)

        self.notifier.send_message(f"Found products in {restaurant.name}: {len(products)}")

        return products

    async def __get_initial_state(self, url: str) -> dict[str, Any]:

        async with self.limit, self.session.get(url, headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0",
        }, ssl=False) as response:

            text = await response.text()

            soup = BeautifulSoup(text, features="html.parser")
            body = soup.find("body")
            scripts = body.find_all("script")

            initial_state: str = scripts[1].text[25:]

            await asyncio.sleep(self.rate)

            try:
                initial_state = json.loads(initial_state)
            except Exception as e:
                self.notifier.send_message(f"An error ocurred: {e}")

            return initial_state
