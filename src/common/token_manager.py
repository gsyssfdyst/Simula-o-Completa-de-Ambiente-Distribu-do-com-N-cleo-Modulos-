import jwt
import time
from datetime import datetime, timedelta, timezone
from src.config import TOKEN_SECRET_KEY, TOKEN_EXPIRATION_SECONDS

class TokenManager:
    @staticmethod
    def generate_token(node_id):
        """Gera um token para um nó específico."""
        payload = {
            'node_id': node_id,
            'exp': datetime.now(timezone.utc) + timedelta(seconds=TOKEN_EXPIRATION_SECONDS)
        }
        return jwt.encode(payload, TOKEN_SECRET_KEY, algorithm="HS256")

    @staticmethod
    def validate_token(token):
        """Valida um token. Retorna o payload se válido, None caso contrário."""
        try:
            payload = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            print("Token has expired.")
            return None
        except jwt.InvalidTokenError:
            print("Invalid token.")
            return None

    @staticmethod
    def access_sensitive_data(token):
        """Simula o acesso a um recurso protegido."""
        payload = TokenManager.validate_token(token)
        if payload:
            print(f"Node {payload['node_id']} accessed sensitive data.")
            return True
        else:
            print("Access to sensitive data denied.")
            return False
