import urllib.request
import urllib.parse

from flask_sqlalchemy import SQLAlchemy


class Notifier:
    def __init__(self, token: str, chat_id: str) -> None:
        self.token = token
        self.chat_id = chat_id

    def send_message(self, message: str) -> None:
        message = urllib.parse.quote(message)

        with urllib.request.urlopen(f"https://api.telegram.org/bot{self.token}/sendMessage?chat_id={self.chat_id}&parse_mode=html&text={message}") as response:
            ...


def get_or_create(db: SQLAlchemy, model, **kwargs) -> tuple:
    instance: model = db.session.query(model).filter_by(**kwargs).first()

    if instance:
        return (instance, False)
    
    instance = model(**kwargs)

    db.session.add(instance)
    # db.session.commit()

    return (instance, True)


def is_ajax(request) -> bool:
    return request.headers.get("X-Requested-With", "") == "XMLHttpRequest"
