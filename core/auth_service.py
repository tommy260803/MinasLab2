import os
import bcrypt
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from core.db_manager import SessionLocal
from sqlalchemy import text

load_dotenv()

JWT_SECRET = os.getenv('JWT_SECRET', 'fallback_secret_for_development')
JWT_EXPIRATION_HOURS = 24

def hash_password(password: str) -> str:
    """Hashea una contraseña con bcrypt y salt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña ingresada coincide con el hash almacenado."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_jwt(user_id: int, username: str, role_id: int) -> str:
    """Genera un token JWT seguro con vigencia limitada."""
    payload = {
        'user_id': user_id,
        'username': username,
        'role_id': role_id,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def decode_jwt(token: str):
    """Decodifica y valida un token JWT."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def authenticate_user(username: str, password: str):
    """
    Autentica un usuario validando credenciales contra la BD.
    Retorna (True, "Mensaje", (token, user_data)) o (False, "Error", None)
    """
    try:
        with SessionLocal() as session:
            query = text("""
                SELECT id, username, password_hash, role_id, is_active 
                FROM users WHERE username = :username
            """)
            result = session.execute(query, {"username": username}).fetchone()
            
            if not result:
                return False, "Usuario o contraseña incorrectos", None
                
            user_id, db_username, db_pass_hash, role_id, is_active = result
            
            if not is_active:
                return False, "La cuenta de usuario está inactiva", None
                
            if not verify_password(password, db_pass_hash):
                return False, "Usuario o contraseña incorrectos", None
                
            # Autenticación exitosa
            token = generate_jwt(user_id, db_username, role_id)
            
            user_data = {
                "id": user_id,
                "username": db_username,
                "role_id": role_id
            }
            return True, "Autenticación exitosa", (token, user_data)
            
    except Exception as e:
        print(f"Error de base de datos en autenticación: {e}")
        return False, "Error interno del servidor", None
