from passlib.context import CryptContext
from passlib.exc import UnknownHashError

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        ok, _ = pwd_context.verify_and_update(plain, hashed)
        return ok
    except UnknownHashError:
        prefix = "hashed::"
        if isinstance(hashed, str) and hashed.startswith(prefix):
            legacy_plain = hashed[len(prefix):]
            return plain == legacy_plain
        return False
