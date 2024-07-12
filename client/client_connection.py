import socket
from client_utils import *

class client:
    def __init__(self, MCAST_GRP, MCAST_PORT, PORT):
        self.MCAST_GRP=MCAST_GRP
        self.MCAST_PORT=MCAST_PORT
        self.PORT=PORT
        self.SERVER_IP=None
        self.search_server()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    def search_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        print("Buscando servidor...")
        sock.sendto(b"DISCOVER", (self.MCAST_GRP, self.MCAST_PORT))
        # Esperar respuesta del servidor
        try:
            data, server = sock.recvfrom(1024)
            self.SERVER_IP = data.decode().split('\1')[1]
            print(f"Servidor encontrado en {self.SERVER_IP}")
        except socket.timeout:
            print("No se encontró ningún servidor")
            exit()

    def connect(self,message):
        # Crear socket unicast para comunicaciones futuras
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Enviar mensajes al servidor usando la dirección unicast
        sock.sendto(message.encode(), (self.SERVER_IP, self.PORT))        
        # Esperar respuesta
        self.sock.settimeout(5)
        try:
            data, _ = sock.recvfrom(1024)
            return data.decode()
        except socket.timeout:
            self.search_server()
            return self.connect(message)

        
    def search(self,query):
        return self.connect(f"QUERY\1{query}")

    def create_agent(self,agent):
        info=get_agent_info(agent)
        if info==None:
            return "ERROR\1El agente no tiene el formato deseado"
        
        #if ya esta creado: print("El agente ya esta creado") return
        response=self.connect(f"CREATE\1{str(info)}")
        decode_response=response.split('\1')
        if decode_response[0]=='ERROR':
           return response
        #Crear hilo con la funcion run_agent
        return response
    
    def run_agent(self):
        """
        """
        #Abre un servidor, busca el IP local y crea