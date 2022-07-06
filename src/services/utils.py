from flask_sqlalchemy import SQLAlchemy

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
