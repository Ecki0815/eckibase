def register_adapters(app):
    from .alexa import register_routes as register_alexa

    register_alexa(app)
