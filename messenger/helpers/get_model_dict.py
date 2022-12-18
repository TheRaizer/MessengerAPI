def get_model_dict(model):
    """Given a model instance, generate a dict mapping column, name to value.

    Args:
        model (_type_): the instance of a Schema

    Returns:
        _type_: a dictionary mapping column, name to value.
    """
    return dict(
        (column.name, getattr(model, column.name))
        for column in model.__table__.columns
    )
