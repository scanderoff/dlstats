import json

from flask import Blueprint, render_template, request
from flask_sqlalchemy import BaseQuery

from .models import db, City, Restaurant, Product
from .services.utils import is_ajax


main = Blueprint("main", __name__)


@main.route("/", methods=["GET"])
def products() -> str:
    cities: list[City] = db.session.query(City).all()
    restaurants: list[Restaurant] = db.session.query(Restaurant).all()

    products: BaseQuery = db.session.query(Product).order_by(Product.updated_at.desc())
    print(products)
    city_ids: list[str] = request.args.getlist("cities")
    restaurant_ids: list[str] = request.args.getlist("restaurants")
    s: str = request.args.get("s", "")

    if city_ids:
        products = products.join(Restaurant).join(City).filter(City.id.in_(city_ids))

    if restaurant_ids:
        products = products.filter(Product.restaurant_id.in_(restaurant_ids))

    if s:
        products = products.filter(Product.name.contains(s))

    total_products: int = products.count()

    page = int(request.args.get("page", "1"))

    products = products.paginate(page, 52, False).items

    if is_ajax(request):
        return render_template("_product_loop.html",
            products=products,
        )

    return render_template("products.html", **{
        "cities": cities,
        "restaurants": restaurants,
        "products": products,
        "total_products": total_products,
    })


@main.route("/product/<int:product_id>/", methods=["GET"])
def product(product_id: int) -> str:
    product: Product = db.session.query(Product).get(product_id)

    # pp - product price
    pp_history = product.price_history
    dates: list[str] = [pp.date.strftime("%d.%m.%Y") for pp in pp_history]
    values: list[float] = [pp.value for pp in pp_history]

    chart: dict[str, str] = {
        "labels": json.dumps(dates),
        "values": json.dumps(values),
    }

    return render_template("product.html", **{
        "product": product,
        "chart": chart,
    })


@main.route("/test/", methods=["GET"])
def test() -> str:
    prod = db.session.query(Product).get(1000)

    prod.price = 9999.0
    db.session.commit()

    return "fdsf"
