from passlib.context import CryptContext

# Configura il contesto di hashing della password
# Utilizzeremo bcrypt come schema di default
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica una password in chiaro rispetto a una password hashata.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Genera l'hash di una password.
    """
    return pwd_context.hash(password)
