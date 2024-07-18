import socket

def send_message(sock, message, addr):
    chunk_size = 1024
    for i in range(0, len(message), chunk_size):
        print("Server sending")
        chunk = message[i:i+chunk_size]
        sock.sendto(chunk, addr)
    sock.sendto(b"END", addr)

def receive_message(sock):
    chunks = []
    while True:
        print("executing")
        chunk, addr = sock.recvfrom(1024)
        if chunk == b"END":
            break
        print(f"Server receive {chunk}")
        chunks.append(chunk)
    data = b''.join(chunks)
    return data, addr

def receive_multiple_messages(sock):
    datas = {}
    while True:
        chunk, addr = sock.recvfrom(1024)

        if chunk == b"END":
            data = b''.join(datas[addr])
            yield data, addr
            del datas[addr]

        elif addr in datas:
            datas[addr].append(chunk)
        else:
            datas[addr] = []
            datas[addr].append(chunk)