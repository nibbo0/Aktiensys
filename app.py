from quart import Quart


def create_app(config=None):
    app = Quart(__name__, static_folder='static', template_folder='templates')

    from frontend import front
    app.register_blueprint(front)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
