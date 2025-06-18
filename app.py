from quart import Quart


def create_app(config=None):
    app = Quart(__name__, static_folder='static', template_folder='templates')

    app.config.from_pyfile('default_config.py')
    app.config.from_pyfile('config.py', silent=True)
    if config is not None:
        app.config.update(**config)

    from frontend import front
    app.register_blueprint(front)

    import db
    db.init_app(app)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
