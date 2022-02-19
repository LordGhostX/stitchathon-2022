import bcrypt


def gensalt():
    return bcrypt.gensalt()


def hash_password(password):
    return bcrypt.hashpw(password.encode(), gensalt()).decode()


def verify_hash(password, password_hash):
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except:
        return False
