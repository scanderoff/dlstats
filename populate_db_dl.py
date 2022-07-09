import asyncio
import dotenv
import requests
import urllib.parse
from typing import Coroutine

from flask import Flask

from src import create_app
from src.models import db, City, Restaurant, Product, ProductPrice
from src.services import delivery_club as dl
from src.services.utils import get_or_create


async def main() -> Coroutine[None, None, None]:
    city_names: list[str] = ["Иркутск"]

    limit = asyncio.Semaphore(3)
    rate = 7.0

    async with dl.Parser(limit, rate) as p:
        cities: list[dl.City] = await p.get_cities(city_names)

        tasks: list[Coroutine] = [p.get_restaurants(city) for city in cities]
        cities_restaurants: list[list[dl.Restaurant]] = await asyncio.gather(*tasks)

        for city, restaurants in zip(cities, cities_restaurants):
            dbcity, _ = get_or_create(db, City, name=city.name)
            db.session.commit()
  
            # tasks = [p.get_products(restaurants[0]), p.get_products(restaurants[1])]
            tasks = [p.get_products(restaurant) for restaurant in restaurants]
            restaurants_products: list[list[dl.Product]] = await asyncio.gather(*tasks)

            for restaurant, products in zip(restaurants, restaurants_products):
                dbrest, _ = get_or_create(
                    db,
                    Restaurant,
                    city=dbcity,
                    name=restaurant.name,
                )

                db.session.commit()

                for product in products:
                    dbprod, _ = get_or_create(
                        db,
                        Product,
                        restaurant=dbrest,
                        internal_id=product.id,
                    )

                    if dbprod.price != product.price:
                        db.session.add(ProductPrice(product=dbprod, value=product.price))

                        dbprod.name = product.name
                        dbprod.description = product.description
                        dbprod.image = product.image
                        dbprod.price = product.price
                        dbprod.weight = product.weight

                db.session.commit()

    db.session.close()


if __name__ == "__main__":
    token = "5499393500:AAETLacc9Xcfk2h5m0TMCeuBD5__clJz4v4"
    chat_id = -639281506
    message: str = urllib.parse.quote("Task started")
    requests.get(f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&parse_mode=html&text={message}")


    dotenv.load_dotenv(".env")

    app: Flask = create_app()
    app.app_context().push()

    asyncio.run(main())
