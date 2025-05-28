import hashlib


def get_url_fingerprint_code(url):
    return hashlib.md5(url.encode()).hexdigest()