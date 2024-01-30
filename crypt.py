import bcrypt


def encrypt_password(password: str):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password


def check_password(password: str, hashed_password: bytes) -> bool:
    if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
        return True
    else:
        return False
