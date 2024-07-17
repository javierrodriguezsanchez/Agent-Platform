import bisect
import hashlib

def get_successor_for_data(collection, element):
    return bisect.bisect_left(collection, element)

def hash(key):
    return int(hashlib.sha1(key.encode()).hexdigest(), 16)