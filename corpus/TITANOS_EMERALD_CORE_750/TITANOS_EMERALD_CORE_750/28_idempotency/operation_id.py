import hashlib
def operation_id(namespace, key):
    return hashlib.sha256(f"{namespace}:{key}".encode()).hexdigest()
