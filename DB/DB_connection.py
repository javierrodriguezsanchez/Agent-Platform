import socket
import struct
import threading
import ast

default_ip='172.17.0.2'

class DB_connection:
    def __init__(self,port,mcast_port,mcast_grp):
        self.IP = socket.gethostbyname(socket.gethostname())
        self.PORT=port
        self.MCAST_PORT=mcast_port
        self.MCAST_GRP=mcast_grp
        print(f"Creando nodo en IP {self.IP}")

        nodes=self.connect('GET_NODES')
        if nodes==None:
            self.NODES=[]
        else:
            print(nodes)
            self.NODES=ast.literal_eval(nodes)
            self.join()
        self.NODES.append(self.IP)
        print(f"Lista de nodos actuales: {self.NODES}")
        self.lock = threading.Lock()
        
        self.run()


    def mcast_run(self):
        print(f"Escuchando multicast por puerto {self.MCAST_PORT}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(('', self.MCAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)

        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while True:
            data, addr = sock.recvfrom(1024)
            print(f"mensaje multicast recibido de {addr}: {data.decode()}")
            print(f"Enviandole mi IP {self.IP}")
            # Enviar respuesta
            sock.sendto(self.IP.encode(), addr)
    
    def run(self):
        print(f"Escuchando por puerto {self.PORT}")
        mcast_thread=threading.Thread(target=self.mcast_run)
        mcast_thread.start()

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self.PORT))
        
        while True:
            data, addr = sock.recvfrom(1024)
            print(f"Mensaje recibido de {addr}: {data.decode()}")
            
            # Crear un nuevo hilo para manejar la interacción del cliente
            answer_thread = threading.Thread(target=self.answer, args=(data, addr, sock))
            answer_thread.start()

    def answer(self, data, addr, sock):
        answer=''
        messege=data.decode()
        if messege=='GET_NODES':
            with self.lock:
                print(self.NODES)
                answer=str(self.NODES)
        if messege=='INSERT':
            ip,_ = addr
            with self.lock:
                self.NODES.append(ip)
                print(f"Lista de nodos actualizada: {self.NODES}")
        sock.sendto(answer.encode(), addr)

    def search_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        sock.sendto(b"DISCOVER", (self.MCAST_GRP, self.MCAST_PORT))
        # Esperar respuesta del servidor
        sock.settimeout(5)
        try:
            data, server = sock.recvfrom(1024)
            ip = data.decode()
            return ip
        except socket.timeout:
            return None

    def connect(self,message,ip=default_ip):
        while True:
            if ip==None:
                ip=self.search_server()
                if ip==None:
                    return None
            # Crear socket unicast para comunicaciones futuras
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Enviar mensajes al servidor usando la dirección unicast
            sock.sendto(message.encode(), (ip, self.PORT))        
            # Esperar respuesta
            
            sock.settimeout(5)
            try:
                data, _ = sock.recvfrom(1024)
                return data.decode()
            except socket.timeout:
                ip=None

    def join(self):
        join_threads=[]
        for ip in self.NODES:
            join_threads.append(threading.Thread(target=self.connect, args=('INSERT',ip)))
            join_threads[-1].start()
            