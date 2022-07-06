import json

from flask import Blueprint, render_template, request

from .models import db, City, Restaurant, Product, ProductPrice
from .services.utils import is_ajax


main = Blueprint("main", __name__)


@main.route("/", methods=["GET"])
def products() -> str:
    cities: list[City] = db.session.query(City).all()
    restaurants: list[Restaurant] = db.session.query(Restaurant).all()
    products: list[Product] = db.session.query(Product)

    city_ids: list[str] = request.args.getlist("cities")
    restaurant_ids: list[str] = request.args.getlist("restaurants")
    s: str = request.args.get("s", "")

    if city_ids:
        products = products.join(Restaurant).join(City).filter(City.id.in_(city_ids))

    if restaurant_ids:
        products = products.filter(Product.restaurant_id.in_(restaurant_ids))

    if s:
        products = products.filter(Product.name.contains(s))
    
    if is_ajax(request):
        return render_template("_product_loop.html",
            products=products,
        )

    return render_template("homepage.html",
        cities=cities,
        restaurants=restaurants,
        products=products[:52],
    )

@main.route("/product/<int:product_id>/", methods=["GET"])
def product(product_id: int) -> str:
    product: Product = db.session.query(Product).get(product_id)

    # pp - product price
    dates: list[str] = [pp.date.strftime("%d.%m.%Y") for pp in product.price_history]
    values: list[float] = [pp.value for pp in product.price_history]

    chart: dict[str, str] = {
        "labels": json.dumps(dates),
        "values": json.dumps(values),
    }

    return render_template("product.html",
        product=product,
        chart=chart,
    )
