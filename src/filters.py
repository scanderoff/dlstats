from .views import main


@main.app_template_filter()
def pretty_price(price: float) -> str:
    return f"{price:,.2f}"
