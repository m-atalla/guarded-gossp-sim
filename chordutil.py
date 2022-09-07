from const import UPPER_BOUND


def chord_range(a: int, b: int) -> range:
    if a <= b:
        return range(a, b)
    else:
        return range(b, a)

def in_chord_range(query: int, a:int , b: int) -> bool:
    diff_query = b - query
    diff_interval = b - a
    return diff_query < diff_interval

def exclusive_interval(query: int, a: int, b: int) -> bool:
    diff_query = b - query
    diff_interval = b - a
    return diff_query < diff_interval

