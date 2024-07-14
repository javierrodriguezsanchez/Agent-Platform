import socket
import struct
import threading
import ast

default_ip=['172.17.0.2']

class DB_connection:
    def __init__(self,port,mcast_port,mcast_grp):
        # Basic information about the node
        self.IP = socket.gethostbyname(socket.gethostname())
        self.PORT=port
        self.MCAST_PORT=mcast_port
        self.MCAST_GRP=mcast_grp
        print(f"Creando nodo en IP {self.IP}")

        # Gets the information about the rest of the nodes
        # ------------------------------------------------
        self.NODES=[]
        for ip in default_ip:
            #using cache nodes
            nodes=self.connect('GET_NODES',ip)
            if nodes!=None:
                break

        if nodes==None:
            #using multicast
            ip=self.search_nodes()
            if ip != None:
                nodes=self.connect('GET_NODES',ip)
        
        if nodes!=None:
            print(nodes)
            self.NODES=ast.literal_eval(nodes)
            self.join()
        else:
            print("No se pudo hallar ningun nodo")
        self.NODES.append(self.IP)
        print(f"Lista de nodos actuales: {self.NODES}")

        #Running the server and the heartbeats
        #-------------------------------------
        self.lock = threading.Lock()
        hearbeat_thread=threading.Thread(target=self.heartbeats)
        hearbeat_thread.start()
        self.run()


    def search_nodes(self):
        '''
            Try to discover other nodes via multicast. Return false if nobody answer
        '''
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

    def connect(self,messege,ip):
        '''
            Send the messege to the ip
        '''
        # Crear socket unicast para comunicaciones futuras
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Enviar mensajes al servidor usando la dirección unicast
        sock.sendto(messege.encode(), (ip, self.PORT))        
        # Esperar respuesta        
        sock.settimeout(5)
        try:
            data, _ = sock.recvfrom(1024)
            return data.decode()
        except socket.timeout:
            return None

    def mcast_run(self):
        '''
            Multicast listening. Make the node able to be discovered
        '''
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
        """
            Mount the server to listen messeges
        """
        print(f"Escuchando por puerto {self.PORT}")

        # Starting multicast server thread
        mcast_thread=threading.Thread(target=self.mcast_run)
        mcast_thread.start()

        # Starting normal server
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self.PORT))
        
        while True:
            data, addr = sock.recvfrom(1024)
            
            # Crear un nuevo hilo para manejar la interacción del cliente
            answer_thread = threading.Thread(target=self.answer, args=(data, addr, sock))
            answer_thread.start()

    def answer(self, data, addr, sock):
        """
            Gives the response to the client
        """
        messege=data.decode()
        answer=self.create_response(messege, addr)
        sock.sendto(answer.encode(), addr)

    def heartbeats(self):
        while True:
            to_remove=[]
            ips=[]
            with self.lock:
                ips=[ip for ip in self.NODES if ip!=self.IP]
            for ip in ips:
                response=self.connect('ALIVE',ip)
                if response==None:
                    to_remove.append(ip)
                    print(f"Node in ip {ip} doesn't found")
            if len(to_remove)>0:
                ips=[x for x in ips if x not in to_remove]
                with self.lock:
                    self.NODES=ips+[self.IP]
                print(f"Lista de adyacentes actualizada: {ips}")


    def create_response(self, messege, addr):
        '''
            Creates the response acording to the messege
        '''
        answer=''
        if messege=='GET_NODES':
            ips=[]
            with self.lock:
                ips=self.NODES
            print(ips)
            answer=str(ips)
        if messege=='INSERT':
            ip,_ = addr
            with self.lock:
                self.NODES.append(ip)
                ips=self.NODES
            print(f"Lista de nodos actualizada: {ips}")
        return answer

    def join(self):
        join_threads=[]
        for ip in self.NODES:
            join_threads.append(threading.Thread(target=self.connect, args=('INSERT',ip)))
            join_threads[-1].start()
            
