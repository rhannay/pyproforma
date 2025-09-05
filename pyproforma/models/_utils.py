import re


def check_name(name) -> bool:
    if not re.match(r"^[A-Za-z0-9_-]+$", name):
        return False
    return True
