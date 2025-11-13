import bcrypt

def make_hash_pass(password: str):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    hashed_password = hashed_password.decode('utf-8')
    return hashed_password


def verify_pass(password: str,hash_pass: str):
    return bcrypt.checkpw(password.encode('utf-8'), hash_pass.encode('utf-8'))