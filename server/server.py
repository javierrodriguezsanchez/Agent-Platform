import socket
import struct
import threading

class server:
    def __init__(self,GRP,PORT1,PORT2):
        self.MCAST_GRP = GRP
        self.MCAST_PORT = PORT1
        self.PORT=PORT2
        self.IP=socket.gethostbyname(socket.gethostname())
        
        #to edit
        self.database=[]
    
    def mcast_run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(('', self.MCAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)

        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        print("Servidor multicast esperando mensajes...")
        while True:
            data, addr = sock.recvfrom(1024)
            # Enviar respuesta
            sock.sendto(f'SUCESS\1{self.IP}'.encode(), addr)
    
    def run(self):
        mcast_thread=threading.Thread(target=self.mcast_run)
        mcast_thread.start()

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self.PORT))
        
        print("Servidor unicast esperando mensajes...")

        while True:
            data, addr = sock.recvfrom(1024)
            print(f"Mensaje recibido de {addr}: {data.decode()}")
            
            # Crear un nuevo hilo para manejar la interacción del cliente
            client_thread = threading.Thread(target=self.handle_client, args=(data, addr, sock))
            client_thread.start()

    def handle_client(self, data, addr, sock):
        print(f"Mensaje recibido de {addr}: {data.decode()}")
        messege=data.decode().split('\1')
        response='ERROR\1Protocolo incorrecto'
        if messege[0]=='QUERY':
            response=self.give_agents(messege[1])
        elif messege[0]=='EXEC':
            response=self.exec_action(messege[1],messege[2],messege[3])
        elif messege[0]=='CREATE':
            self.database.append((messege[1], addr))
        
        # Enviar respuesta
        print(f'Enviando {response} a {addr}')
        sock.sendto(f'SUCESS\1{response}'.encode(), addr)

    def give_agents(self,query): 
        #NOTE: CHANGE BY CONNECTION WITH DATABASE
        return str([x for x,_ in self.database])
    
    def exec_action(self,agent,action,args):
        '''
            To edit when distribute
        try:
            with open(f'Agents/{agent}/{action}/Run.y', 'r') as archivo:
                codigo_python = archivo.read()
            return codigo_python
        except FileNotFoundError:
            print(f"Error: El archivo no se encontró.")
        except IOError:
            print("Error: Ocurrió un problema al leer el archivo.")
        except Exception as e:
            print(f"Error inesperado: {e}")
            raise
        '''
        return '2'