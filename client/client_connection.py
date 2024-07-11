import socket
import time

class client:
    def __init__(self,MCAST_GRP,MCAST_PORT):
        self.MCAST_GRP=MCAST_GRP
        self.MCAST_PORT=MCAST_PORT
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    def connect(self,message):
        self.sock.sendto(message.encode(), (self.MCAST_GRP, self.MCAST_PORT))
        print(f"Mensaje enviado: {message}")
        # Esperar respuesta
        self.sock.settimeout(5)
        try:
            data, server = self.sock.recvfrom(1024)
            return data.decode()
        except socket.timeout:
            return 'ERROR\1TIMEOUT'