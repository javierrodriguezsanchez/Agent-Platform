import hashlib


def send_message(sock, message, addr):
    chunk_size = 1024
    sock.sendto(b"\6", addr)
    for i in range(0, len(message), chunk_size):
        chunk = message[i:i+chunk_size]
        sock.sendto(chunk, addr)
    sock.sendto(b"\7", addr)

def receive_message(sock):
    chunks = []
    sock.settimeout(10)
    while True:
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


def is_successor(ip, new_ip, successor):
    normal_case = ip < new_ip  and  new_ip < successor
    no_other_node_case = ip==successor
    corner_case_1 = successor < ip  and  ip < new_ip
    corner_case_2 = successor < ip  and  new_ip < successor
    return normal_case or no_other_node_case or corner_case_1 or corner_case_2


def hash(key):
    return int(hashlib.sha1(key.encode()).hexdigest(), 16)