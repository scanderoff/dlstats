import os
import asyncio
import dotenv
from typing import Coroutine

from flask import Flask

from src import create_app
from src.models import db, City, Restaurant, Product, ProductPrice
from src.services import delivery_club as dl
from src.services.utils import Notifier, get_or_create


async def main() -> Coroutine[None, None, None]:
    city_names: list[str] = ["Иркутск"]

    limit = asyncio.Semaphore(3)
    rate = 20.0

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
    dotenv.load_dotenv(".env")



    # token: str = os.getenv("TELEGRAM_BOT_TOKEN")
    # chat_id: str = os.getenv("TELEGRAM_CHAT_ID")
    # Notifier(token, chat_id).send_message("Task started")



    app: Flask = create_app()
    app.app_context().push()

    asyncio.run(main())
