import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


db = SQLAlchemy()
migrate = Migrate()


class City(db.Model):
    __tablename__ = "city"

    id = db.Column(db.Integer, primary_key=True, index=True, unique=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    restaurants = db.relationship("Restaurant", backref="city")


class Restaurant(db.Model):
    __tablename__ = "restaurant"
    __table_args__ = (
        db.UniqueConstraint("city_id", "name", name="city_restaurant_uc"),
    )

    id = db.Column(db.Integer, primary_key=True, index=True, unique=True)
    city_id = db.Column(db.Integer, db.ForeignKey("city.id"), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    products = db.relationship("Product", backref="restaurant")


class Product(db.Model):
    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True, index=True, unique=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurant.id"), nullable=False)
    internal_id = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(128))
    description = db.Column(db.String(512))
    price = db.Column(db.Float)
    image = db.Column(db.String(256))
    weight = db.Column(db.String(64))
    price_history = db.relationship(
        "ProductPrice",
        backref=db.backref("product", lazy="joined"),
        order_by="ProductPrice.date",
        lazy="joined",
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow, nullable=False
    )
    
    @property
    def price_dropped(self) -> bool | None:
        history = self.price_history

        if len(history) < 2:
            return None

        return history[-1].value < history[-2].value

    def get_image_url(self, width: int, height: int) -> str:
        if not self.image:
            return "https://yastatic.net/s3/eda-front/www/assets/desktop.light.a623a0604d5b8e0630de.svg"

        return "https://eda.yandex.ru" + self.image.replace("{w}", str(width)).replace("{h}", str(height))


class ProductPrice(db.Model):
    __tablename__ = "product_price"

    id = db.Column(db.Integer, primary_key=True, index=True, unique=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    value = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=datetime.date.today, nullable=False)

    def __repr__(self) -> str:
        date: str = self.date.strftime("%d.%m.%Y")

        return f"{self.product.name} {self.value} ₽ ({date})"


# select product_id, COUNT(*) from product_price group by product_id having COUNT(*) > 1