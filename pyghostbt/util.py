import hashlib
import random
from datetime import datetime


def uuid():
    """
    generate uuid
    :return: the uuid len 32
    """
    m = hashlib.md5()
    m.update("{}{}".format(
        datetime.now().timestamp(),
        random.randint(1, 10000),
    ).encode())
    return m.hexdigest()
