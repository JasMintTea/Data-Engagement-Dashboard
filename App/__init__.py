from .models import *
from .views import *
from .controllers import *
from .main import *
from App.views import auth_views
from flask_jwt_extended import JWTManager


def create_app():
    app = Flask(__name__)

    # ... config ...
    jwt = JWTManager(app)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return User.query.get(identity)

    # Register blueprints
    from App.views.auth_views import auth_blueprint
    app.register_blueprint(auth_blueprint)


    views = [auth_views]

    return app