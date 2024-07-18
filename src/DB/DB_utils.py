import bisect
import socket
import hashlib

def get_successor(collection, element):
    return bisect.bisect_left(collection, element)

def send_message(sock, message, addr):
    chunk_size = 1024
    sock.sendto(b"START", addr)
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
        if chunk == b"START":
            continue
        chunks.append(chunk)
        
    data = b''.join(chunks)
    return data, addr

def receive_multiple_messages(sock):
    datas = {}
    while True:
        chunk, addr = sock.recvfrom(1024)

        a=chunk.decode()
        if('END' in a and a!='END'):
            print(a)

        if chunk == b"START":
            datas[addr] = []
            continue

        if chunk == b"END":
            data = b''.join(datas[addr])
            yield data, addr
            del datas[addr]

        elif addr in datas:
            datas[addr].append(chunk)
        else:
            datas[addr] = []
            datas[addr].append(chunk)

def hash(key):
    return int(hashlib.sha1(key.encode()).hexdigest(), 16)