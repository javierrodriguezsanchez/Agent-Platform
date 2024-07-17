import socket
import struct
import threading
import ast
from server_utils import *

default_db_ip=['172.17.0.2']
default_db_grp='224.1.1.2'
default_db_port=5008
default_db_mcast_port=5009

class server:
    def __init__(self,GRP,PORT1,PORT2,AGENTS_PORT):
        self.MCAST_GRP = GRP
        self.MCAST_PORT = PORT1
        self.PORT=PORT2
        self.AGENTS_PORT=AGENTS_PORT
        self.IP=socket.gethostbyname(socket.gethostname())
        self.DB_IP=default_db_ip[0]
        self.DB_GRP=default_db_grp
        self.DB_PORT=default_db_port
        self.DB_MCAST_PORT=default_db_mcast_port

    def mcast_run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(('', self.MCAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)

        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        print("Servidor multicast esperando mensajes...")
        for data, addr in receive_multiple_messages(sock):
            #_, addr = receive_message(sock)
            # Enviar respuesta
            #sock.sendto(f'SUCESS\1{self.IP}'.encode(), addr)
            send_message(sock, f'SUCESS\1{self.IP}'.encode(), addr)
    
    def run(self):
        mcast_thread=threading.Thread(target=self.mcast_run)
        mcast_thread.start()

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self.PORT))
        
        print("Servidor unicast esperando mensajes...")

        for data, addr in receive_multiple_messages(sock):
            #data, addr = receive_message(sock)
            print(f"Mensaje recibido de {addr}: {data.decode()}")
            
            # Crear un nuevo hilo para manejar la interacción del cliente
            client_thread = threading.Thread(target=self.handle_client, args=(data, addr, sock))
            client_thread.start()

    def db_configure(self, GRP,PORT, MCAST_PORT):
        self.DB_GRP=GRP
        self.DB_PORT=PORT
        self.DB_MCAST_PORT=MCAST_PORT
        
    def search_db(self):
        '''
            Use multicast to search the DB
        '''
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        print("Buscando servidor...")
        #sock.sendto(b"DISCOVER", (self.DB_GRP, self.DB_MCAST_PORT))
        send_message(sock, b"DISCOVER",(self.DB_GRP, self.DB_MCAST_PORT))
        # Esperar respuesta del servidor
        try:
            data, _ = receive_message(sock)
            self.DB_IP = data.decode()
            print(f"Base de datos encontrada en {self.DB_IP}")
        except socket.timeout:
            print("No se encontró ningún servidor")
            exit()

    def connect_database(self,message):
        # Crear socket unicast para comunicaciones futuras
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Enviar mensajes al servidor usando la dirección unicast
        #sock.sendto(message.encode(), (self.DB_IP, self.DB_PORT)) 
        send_message(sock, message.encode(), (self.DB_IP, self.DB_PORT))       
        # Esperar respuesta
        
        sock.settimeout(5)
        try:
            data, _ = receive_message(sock)
            return data.decode()
        except socket.timeout:
            self.search_db()
            return self.connect_database(message)

    def handle_client(self, data, addr, sock):
        sucess=True
        response=''
        messege=data.decode().split('\1')
        
        if messege[0]=='QUERY':
            response=self.connect_database(f"GET_AGENTS\1{messege[1]}")

        elif messege[0]=='CREATE':
            response=self.connect_database(f"INSERT_AGENT\1{messege[1]}\1{messege[2]}\1{addr[0]}")
        
        elif messege[0]=='SUBSCRIBE':
            result =self.connect_database(f"INSERT_CLIENT\1{messege[1]}\1{messege[2]}\1{addr[0]}")
            if result=='False':
                response='El usuario ya existe'
                sucess=False

        elif messege[0]=='LOGIN':
            result=self.connect_database(f"CHECK_PASSWORD\1{messege[1]}\1{messege[2]}")
            if result=='False':
                response='Password incorrecto'
                sucess=False

        elif messege[0]=='UPDATE':
            self.connect_database(f"UPDATE_AGENT\1{messege[1]}\1{messege[2]}\1{addr[0]}")

        elif messege[0]=='DELETE':
            self.connect_database(f"REMOVE_AGENTS\1{messege[1]}")

        elif messege[0]=='EXEC':
            ip=self.connect_database(f"GET_IP_AGENT\1{messege[1]}")
            if ip!=None:
                response=self.exec_action(messege[1],messege[2],messege[3],ip)
                response=response.split('\1')
                if response[0]=="ERROR":
                    sucess==False
                    response=response[1]
                else:
                    response=response[1]
            else:
                response="El agente no existe"
                sucess=False
        
        else:
            response='Protocolo incorrecto'
            sucess=False

        # Enviar respuesta
        print(f'Enviando {response} a {addr}')
        result='SUCESS' if sucess else 'ERROR'
        #sock.sendto(f'{result}\1{response}'.encode(), addr)
        send_message(sock, f'{result}\1{response}'.encode(), addr)
    
    def exec_action(self,agent,action,args, IP):
        messege=f'EXEC\1{agent}\1{action}\1{args}'
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Enviar mensajes al servidor usando la dirección unicast
        print(IP)
        print(type(IP))
        print(args)
        print(type(args))
        #sock.sendto(messege.encode(), (IP, self.AGENTS_PORT))        
        send_message(sock, messege.encode(), (IP, self.AGENTS_PORT))     
        # Esperar respuesta
        
        sock.settimeout(5)
        try:
            data, _ = receive_message(sock)
            return data.decode()
        except socket.timeout:
            return 'ERROR\1Time out'