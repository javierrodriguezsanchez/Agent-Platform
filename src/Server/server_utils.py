import socket
import bisect
import hashlib

def get_successor(collection, element):
    return bisect.bisect_left(collection, element)

def hash(key):
    return int(hashlib.sha1(key.encode()).hexdigest(), 16)

def smallest_difference_index(collection):
    smallest=1
    if len(collection)<=2:
        return 0, 0
    smallest_val=collection[2]-collection[0]
    for i in range(2,len(collection)-1):
        if collection[i+1]-collection[i-1]<smallest_val:
            smallest=i
    return smallest

def send_message(sock, message, addr):
    chunk_size = 1024
    sock.sendto(b"\6", addr)
    for i in range(0, len(message), chunk_size):
        chunk = message[i:i+chunk_size]
        sock.sendto(chunk, addr)
    sock.sendto(b"\7", addr)

def receive_message(sock):
    chunks = []
    while True:
        sock.settimeout(10)
        try:
            chunk, _ = sock.recvfrom(1024)
        except:
            return None
        if chunk == b"\7":
            break
        if chunk == b"\6":
            continue
        chunks.append(chunk)
    data = b''.join(chunks)
    return data

def receive_multiple_messages(sock):
    datas = {}
    while True:
        chunk, addr = sock.recvfrom(1024)

        if chunk == b"\6":
            datas[addr] = []
            continue

        if chunk == b"\7":
            data = b''.join(datas[addr])
            yield data, addr
            del datas[addr]

        elif addr in datas:
            datas[addr].append(chunk)
        else:
            datas[addr] = []
            datas[addr].append(chunk)