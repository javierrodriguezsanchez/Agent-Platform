import bisect

def get_successor(collection, element):
    return bisect.bisect_left(collection, element)