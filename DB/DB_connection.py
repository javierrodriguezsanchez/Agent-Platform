import socket
import struct
import threading
import ast
from DB import DB, parseDB
from DB_aux import *
import time

default_ip=['172.17.0.2']

class DB_connection:
    def __init__(self,port,mcast_port,mcast_grp):
        # Basic information about the node
        # --------------------------------
        self.IP = socket.gethostbyname(socket.gethostname())
        self.PORT=port
        self.MCAST_PORT=mcast_port
        self.MCAST_GRP=mcast_grp
        print(f"Creando nodo en IP {self.IP}")

        # Gets the information about the rest of the nodes
        # ------------------------------------------------
        self.NODES=self.get_nodes()

        if self.NODES==[]:
            print("No se pudo hallar ningun nodo")
            self.SUCCESSOR=self.IP
            self.ANTECCESSOR=self.IP
            self.NODES.append(self.IP)
        elif len(self.NODES)==1:
            self.SUCCESSOR=self.NODES[0]
            self.ANTECCESSOR=self.NODES[0]
            if self.NODES[0]>self.IP:
                self.NODES=[self.IP]+self.NODES
            else:
                self.NODES.append(self.IP)
        else:
            successor_pos=get_successor(self.NODES, self.IP)
            self.SUCCESSOR=self.NODES[successor_pos if successor_pos<len(self.NODES) else 0]
            self.ANTECCESSOR=self.NODES[successor_pos-1]
            self.NODES=self.NODES[:successor_pos]+[self.IP]+self.NODES[successor_pos:]
        
        print(f"Lista de nodos actuales: {self.NODES}")
        print(f"Mi sucesor es {self.SUCCESSOR}")
        print(f"Mi antecesor es {self.ANTECCESSOR}")

        #Updating database and finger table
        #----------------------------------
        if len(self.NODES)!=1:
            self.DB_NODE=parseDB(self.connect('MIGRATE',self.SUCCESSOR))
            self.join()
        else:
            self.DB_NODE=DB()

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

    def get_nodes(self):
        '''
            Gets the IP from the nodes in the structure
        '''
        #using cache nodes
        nodes=None
        for ip in default_ip:
            nodes=self.connect('GET_NODES',ip)
            if nodes!=None:
                break

        #using multicast
        if nodes==None:
            ip=self.search_nodes()
            if ip != None:
                nodes=self.connect('GET_NODES',ip)
        
        if nodes==None:
            return []
        return ast.literal_eval(nodes)

    def heartbeats(self):
        while True:
            time.sleep(10)
            to_remove=[]
            ips=[]
            with self.lock:
                ips=self.NODES
            for ip in ips:
                if ip==self.IP:
                    continue
                response=self.connect('ALIVE',ip)
                if response==None:
                    to_remove.append(ip)
                    print(f"Node in ip {ip} doesn't found")
            if len(to_remove)>0:
                ips=[x for x in ips if x not in to_remove]
                with self.lock:
                    self.NODES=ips
                print(f"Lista de adyacentes actualizada: {ips}")

    def create_response(self, messege, addr):
        '''
            Creates the response acording to the messege
        '''
        answer=''
        instruction=messege.split('\1')
        if instruction[0]=='GET_NODES':
            ips=[]
            with self.lock:
                ips=self.NODES
            print(ips)
            answer=str(ips)
        if instruction[0]=='INSERT':
            ip,_ = addr            
            with self.lock:
                ips=self.NODES
            successor=get_successor(ips, ip)
            ips=ips[:successor]+[ip]+ips[successor:]
            with self.lock:
                self.NODES=ips
            print(f"Lista de nodos actualizada: {ips}")
        if instruction[0]=='MIGRATE':
            with self.lock:
                answer=str(self.DB_NODE)
        if instruction[0]=='INSERT_CLIENT':
            with self.lock:
                self.DB_NODE.add_client(instruction[1],instruction[2],instruction[3])
        if instruction[0]=='INSERT_AGENT':
            with self.lock:
                self.DB_NODE.add_agent(instruction[1],instruction[2],instruction[3])
        if instruction[0]=='UPDATE_AGENT':
            with self.lock:
                self.DB_NODE.update_agent(instruction[1],instruction[2])
        if instruction[0]=='CHECK_PASSWORD':
            with self.lock:
                answer = self.DB_NODE.check_password(instruction[1],instruction[2])
        if instruction[0]=='GET_IP_AGENT':
            with self.lock:
                answer = self.DB_NODE.get_ip_agent(instruction[1])
        if instruction[0]=='GET_AGENTS':
            with self.lock:
                answer = self.DB_NODE.get_agents(instruction[1])
        if instruction[0]=='REMOVE_AGENTS':
            with self.lock:
                self.DB_NODE.remove_agent(instruction[1])
            self.remove_copies(instruction[1])
        if instruction[0]=='REMOVE_COPY':
            with self.lock:
                self.DB_NODE.remove_agent(instruction[1])

        return str(answer)

    def join(self):
        join_threads=[]
        for ip in self.NODES:
            if ip==self.IP:
                continue
            join_threads.append(threading.Thread(target=self.connect, args=('INSERT',ip)))
            join_threads[-1].start()
        
        for t in join_threads:
            t.join()

    def remove_copies(self, messege):
        join_threads=[]
        for ip in self.NODES:
            if ip==self.IP:
                continue
            join_threads.append(threading.Thread(target=self.connect, args=(f'REMOVE_COPY\1{messege}',ip)))
            join_threads[-1].start()
        
        for t in join_threads:
            t.join()