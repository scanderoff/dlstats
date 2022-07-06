import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


db = SQLAlchemy()
migrate = Migrate()


class City(db.Model):
    __tablename__ = "city"

    id = db.Column(db.Integer, primary_key=True, index=True, unique=True)
    name = db.Column(db.String, unique=True, nullable=False)
    restaurants = db.relationship("Restaurant", back_populates="city")


class Restaurant(db.Model):
    __tablename__ = "restaurant"
    __table_args__ = (
        db.UniqueConstraint("city_id", "name", name="city_restaurant_uc"),
    )

    id = db.Column(db.Integer, primary_key=True, index=True, unique=True)
    city_id = db.Column(db.Integer, db.ForeignKey("city.id"), nullable=False)
    city = db.relationship("City", back_populates="restaurants")
    name = db.Column(db.String, nullable=False)
    products = db.relationship("Product", back_populates="restaurant")


class Product(db.Model):
    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True, index=True, unique=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"), nullable=False)
    restaurant = db.relationship("Restaurant", back_populates="products")
    internal_id = db.Column(db.Integer, unique=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    price = db.Column(db.Float)
    image = db.Column(db.String)
    weight = db.Column(db.String)
    price_history = db.relationship("ProductPrice", back_populates="product")
    # updated_at = db.Column()

    @property
    def image_url(self) -> str:
        if not self.image:
            return "https://yastatic.net/s3/eda-front/www/assets/desktop.light.a623a0604d5b8e0630de.svg"

        return "https://eda.yandex.ru" + self.image


class ProductPrice(db.Model):
    __tablename__ = "product_price"

    id = db.Column(db.Integer, primary_key=True, index=True, unique=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    product = db.relationship("Product", back_populates="price_history")
    value = db.Column(db.Float)
    date = db.Column(db.Date, default=datetime.date.today, nullable=False)

    def __repr__(self) -> str:
        date: str = self.date.strftime("%d.%m.%Y")

        return f"{self.product.name} {self.value} ₽ ({date})"


# select product_id, COUNT(*) from product_price group by product_id having COUNT(*) > 1