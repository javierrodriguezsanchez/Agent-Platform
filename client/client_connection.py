import socket
from client_utils import *

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