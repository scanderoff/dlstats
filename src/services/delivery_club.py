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

        self.headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Cookie": "amplitude_id_692a3723a9dfa13093b43c500d5c5074delivery-club.ru=eyJkZXZpY2VJZCI6IjM0MDY2ODM2LTVkMTYtNGNlMi1iMDc1LTdkYTQ1NmFmZDAyNFIiLCJ1c2VySWQiOm51bGwsIm9wdE91dCI6ZmFsc2UsInNlc3Npb25JZCI6MTY1NzY1MjI5MDM1MSwibGFzdEV2ZW50VGltZSI6MTY1NzY1MjMxMjc4NiwiZXZlbnRJZCI6ODUsImlkZW50aWZ5SWQiOjY4LCJzZXF1ZW5jZU51bWJlciI6MTUzfQ==; _gcl_au=1.1.819446901.1652365430; ab_experiments_entity_id=QRASDJIiSqCqdsKnSpjztQ; ab_experiments_list=acs-googlepay-ecosys-1075-3%3Atest%3Bdc-pro-v2%3Atest%3Bdcpro-137%3Acontrol%3Becosys-1493-web…xhdGZvcm0iOiJtYXJrZXQiLCJ1c2VySUQiOjAsImRldmljZUlEIjoiNzU4Y2Y4ODEtMGRmOC00MTA0LWIyZjQtZDhkM2JhYWJiMmVkIiwiaW5zdGFsbElEIjoiYmQ0YjBlNmExODk1NDcwNGVjMTEyOWFiOWMzYjIxZDlmMWNhZDRjMSIsImV4cCI6MTY1NzY1MzIwNn0.NirHkMQfAlV4scq1b0IW-UBrnmigaWLfaaLTauYCz-s; split_test_version=version_b; tmr_reqNum=223; tmr_lvid=efe228b96e311229574ba9f78c6bf92c; tmr_lvidTS=1652365431529; client_address=%7B%22cityId%22%3A20%2C%22host%22%3A%22irkutsk%22%2C%22latitude%22%3A52.286387%2C%22longitude%22%3A104.28066%2C%22timeOffset%22%3A5%7D",
            "Host": "www.delivery-club.ru",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0",
        }

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
            }, headers={"User-Agent": self.headers["User-Agent"]}, ssl=False) as response:

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

        async with self.limit, self.session.get(url, headers=self.headers, ssl=False) as response:
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
                
                with open("response.txt", "w") as ouf:
                    ouf.write(text)

            return initial_state
