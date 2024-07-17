import bisect
import socket
import hashlib

def get_successor(collection, element):
    return bisect.bisect_left(collection, element)

def send_message(sock, message, addr):
    chunk_size = 1024
    for i in range(0, len(message), chunk_size):
        chunk = message[i:i+chunk_size]
        sock.sendto(chunk, addr)
    sock.sendto(b"END", addr)

def receive_message(sock):
    chunks = []
    while True:
        chunk, addr = sock.recvfrom(1024)
        if chunk == b"END":
            break
        chunks.append(chunk)
    data = b''.join(chunks)
    return data, addr

def hash(key):
    return int(hashlib.sha1(key.encode()).hexdigest(), 16)