import socket
import struct
import threading

class DB:
    def __init__(self):
        self.users=[]
        self.agents=[]

class server:
    def __init__(self,GRP,PORT1,PORT2):
        self.MCAST_GRP = GRP
        self.MCAST_PORT = PORT1
        self.PORT=PORT2
        self.IP=socket.gethostbyname(socket.gethostname())
        
        #to edit
        self.database=DB()
    
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
        
        sucess=True
        response=''
        messege=data.decode().split('\1')
        
        if messege[0]=='QUERY':
            response=str([x for _,x,_ in self.database.agents])
        
        elif messege[0]=='CREATE':
            self.database.agents.append((messege[1],messege[2], addr))
            response=str(addr)
            print(addr)
        
        elif messege[0]=='SUBSCRIBE':
            if messege[1] in [x[0] for x in self.database.users]:
                response='Un usuario con ese nombre ya existe'
                sucess=False
            else:
                self.database.users.append((messege[1],messege[2]))
        
        elif messege[0]=='LOGIN':
            if (messege[1],messege[2]) not in self.database.users:
                response='Password incorrecto'
                sucess=False

        elif messege[0]=='UPDATE':
            exist=False
            response=str(addr)
            for i in range(len(self.database.agents)):
                if self.database.agents[i][0] == messege[1]:
                    self.database.agents[i]=(messege[1],messege[2],addr)
                    exist=True
                    break
            if not exist:
                self.database.agents.append((messege[1],messege[2], addr))

        elif messege[0]=='DELETE':
            self.database.agents=[x for x in self.database.agents if x[0]!=messege[1]]

        elif messege[0]=='EXEC':
            for i in range(len(self.database.agents)):
                if self.database.agents[i][0] == messege[1]:
                    response=self.exec_action(messege[1],messege[2],messege[3],self.database.agents[i][2])
                    response=response.split('\1')
                    print()
                    print(response)
                    print()
                    if response[0]=="ERROR":
                        sucess==False
                        response=response[1]
                    else:
                        response=response[1]
            if response=='':
                response="El agente no existe"
                sucess=False
        
        else:
            response='Protocolo incorrecto'
            sucess=False

        # Enviar respuesta
        print(f'Enviando {response} a {addr}')
        result='SUCESS' if sucess else 'ERROR'
        sock.sendto(f'{result}\1{response}'.encode(), addr)
    
    def exec_action(self,agent,action,args, addr):
        messege=f'EXEC\1{agent}\1{action}\1{args}'
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Enviar mensajes al servidor usando la dirección unicast
        sock.sendto(messege.encode(), addr)        
        # Esperar respuesta
        
        sock.settimeout(5)
        try:
            data, _ = sock.recvfrom(1024)
            return data.decode()
        except socket.timeout:
            return 'ERROR\1Time out'