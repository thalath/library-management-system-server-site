from flask import Flask
from config import Config
from extensions import db, jwt_manager, cors, migrate
 

def create_app(class_config: type[Config] = Config):
    app = Flask(__name__)
    app.config.from_object(class_config)

    db.init_app(app)
    jwt_manager.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(
        app,
        resources={r"/*": {"origins": "http://127.0.0.1:5173"}},
        # origins="http://127.0.0.1:5173",
        supports_credentials=True
    )
    
    from app.models.token_blocklist import check_if_token_revoked

    from app.routes.user_route import user_bp
    from app.routes.role_route import role_bp
    from app.routes.permission_route import perm_bp
    from app.routes.auth_route import auth_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(role_bp)
    app.register_blueprint(perm_bp)
    app.register_blueprint(auth_bp)

    from app.models.user import User
    from app.models.permission import Permission
    from app.models.role import Role
    from app.models.token_blocklist import TokenBlocklist

    with app.app_context():
        from app.models.token_blocklist import cleanup_expired_tokens
        cleanup_expired_tokens()

    return app
