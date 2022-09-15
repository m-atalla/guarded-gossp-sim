import random
import const

def ip():
    a = u8_int()
    b = u8_int()
    c = u8_int()
    d = u8_int()

    ip = "{}.{}.{}.{}".format(a,b,c,d)

    return (ip, key())

def key() -> int:
    return int(random.uniform(0, const.UPPER_BOUND - 1))

def u8_int():
    return random.randint(0, 255)

def finger_idx() -> int:
    return random.randint(1, const.M_BITS - 1)

def sample_size():
    return random.randint(15, const.MAX_GUARDS)
