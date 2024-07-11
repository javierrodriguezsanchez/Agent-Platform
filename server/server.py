import socket
import struct
import threading

class server:
    def __init__(self,GRP,PORT):
        self.MCAST_GRP = GRP
        self.MCAST_PORT = PORT
    
    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(('', self.MCAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)

        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        print("Servidor multicast esperando mensajes...")

        while True:
            data, addr = sock.recvfrom(1024)
            print(f"Mensaje recibido de {addr}: {data.decode()}")
            
            # Crear un nuevo hilo para manejar la interacción del cliente
            client_thread = threading.Thread(target=self.handle_client, args=(data, addr, sock))
            client_thread.start()

    def handle_client(self, data, addr, sock):
        print(f"Mensaje recibido de {addr}: {data.decode()}")
        messege=data.decode().split('\1')
        response=''
        if messege[0]=='QUERY':
            response=self.GetInfo(messege[1])
        elif messege[0]=='EXEC':
            response=self.GiveAction(messege[1],messege[2],messege[3])

        # Enviar respuesta
        sock.sendto(response.encode(), addr)

    def GetInfo(self,query): 
        #NOTE: CHANGE BY CONNECTION WITH DATABASE
        #return [x.encode("utf-8") for x in self.agents]
        return 'ultimate agent'
    
    def GiveAction(self,agent,action,args):
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