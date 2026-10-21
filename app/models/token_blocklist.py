from extensions import db, jwt_manager
from datetime import datetime, timedelta, timezone

class TokenBlocklist(db.Model):
    __tablename__ = "token_blocklist"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    type = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


@jwt_manager.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    token = db.session.scalar(
            db.select(TokenBlocklist).filter(TokenBlocklist.jti == jti)
    )

    return token is not None


def cleanup_expired_tokens():
    db.session.query(TokenBlocklist).filter(
        TokenBlocklist.type=="access",
        TokenBlocklist.created_at < datetime.utcnow() - timedelta(minutes=20)
    ).delete(synchronize_session=False)


    db.session.query(TokenBlocklist).filter(
        TokenBlocklist.type=="refresh",
        TokenBlocklist.created_at < datetime.utcnow() - timedelta(days=31)
    ).delete(synchronize_session=False)

    db.session.commit()