import socket
import threading
import time
from DB_utils import *
from DB import database

class DB_connection:
    def __init__(self, info):
        self.MCAST_GRP = info['MULTICAST GROUP'] 
        self.MCAST_PORT = info['MULTICAST PORT']
        self.PORT = info['PORT']
        self.IP = socket.gethostbyname(socket.gethostname())
        self.DATABASE=database()

    def run(self):
        #OPEN THE THREADS
        hearbeats_thread=threading.Thread(target=self.heartbeats)
        hearbeats_thread.start()

        #RUNS THE SERVER
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self.PORT))
        print("Servidor unicast esperando mensajes...")
        for data, addr in receive_multiple_messages(sock):
            print(f"Mensaje recibido de {addr}: {data.decode()}")
            # Crear un nuevo hilo para manejar la interacción del cliente
            thread = threading.Thread(target=self.answer, args=(data, addr, sock))
            thread.start()

    def heartbeats(self):
        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.sendto('ALIVE'.encode(), (self.MCAST_GRP, self.MCAST_PORT))
            time.sleep(5)

    def answer(self,data,addr,sock):
        stop_event = threading.Event()
        wait_thread = threading.Thread(target=self.wait, args=(addr, sock, stop_event))
        wait_thread.start()
        response=self.DATABASE.edit_database(data.decode())
        # SEND ANSWER
        stop_event.set()
        wait_thread.join()
        print(f'Enviando {response} a {addr}')
        send_message(sock, response.encode(), addr)


    def wait(self, addr, sock, stop_event):
        try:
            while not stop_event.is_set():
                sock.sendto(b"\6", addr)
        except:
            pass

