import socket
import struct
import threading
import ast
from DB import DB, parseDB
from DB_aux import *
import time

default_ip=['172.17.0.2']

'''
Crear funcion para encontrar sucessor y antecesor
Crear funcion separate y forget en DB
Modificar copias en insercion, modificacion y eliminacion
Hacer el see around y el finger table
'''

class DB_connection:
    def __init__(self,port,mcast_port,mcast_grp):
        # Basic information about the node
        # --------------------------------
        self.IP = socket.gethostbyname(socket.gethostname())
        self.PORT=port
        self.MCAST_PORT=mcast_port
        self.MCAST_GRP=mcast_grp
        self.FINGER_TABLE=[self.IP]*160
        self.DB=DB()
        self.S_COPY=DB()
        self.SS_COPY=DB()
        print(f"Creando nodo en IP {self.IP}")
        self.lock = threading.Lock()

        # Gets the information about the sucessors
        # -----------------------------------------
        self.SUCCESSOR=None
        self.SS=None
        self.SSS=None
        self.get_sucessors()

        # Fill finger table
        # -----------------
        if self.SUCCESSOR!=self.IP:
            ft_thread=threading.Thread(target=self.get_finger_table)
            ft_thread.start()
            self.migrate()
        if self.SUCCESSOR==self.IP:
            print("No se pudo hallar ningun nodo")
            
        print(f"Mi sucesor es {self.SUCCESSOR}")
        print(f"El sucesor de mi sucesor es {self.SS}")
        #Running the server and the heartbeats
        #-------------------------------------
        hearbeat_thread=threading.Thread(target=self.heartbeats)
        hearbeat_thread.start()
        check_copies_thread=threading.Thread(target=self.check_copies)
        check_copies_thread.start()
        upd_ft_thread=threading.Thread(target=self.update_finger_table)
        upd_ft_thread.start()
        self.run()

    def heartbeats(self):
        while True:
            self.mcast_messege('ALIVE')
            self.get_finger_table()
            time.sleep(5)

    def mcast_messege(self,messege):
        '''
            Try to discover other nodes via multicast. Return false if nobody answer
        '''
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        sock.sendto(messege.encode(), (self.MCAST_GRP, self.MCAST_PORT))
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
            data=data.decode()
            print(f"mensaje multicast recibido de {addr}: {data}")
            if data=='ALIVE':
                ip=addr[0]
                if ip>self.IP and ip<self.SUCCESSOR or (self.IP>self.SUCCESSOR and self.IP<ip):
                    self.SUCCESSOR=ip
            else:
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
        answer=''
        instruction=messege.split('\1')
        if instruction[0]=='GET_SUCCESSOR':
            answer=self.get_sucessor_for_data(int(instruction[1]))   
        if instruction[0]=='SUCESSORS':
            answer=self.SUCCESSOR+'\1'+self.SS
        if instruction[0]=='MIGRATE':
            with self.lock:
                answer=str(self.DB)+'\1'+str(self.S_COPY)
        if instruction[0]=='RECOVER_MIDDLE':
            with self.lock:
                answer=str(self.S_COPY)
            thread=threading.Thread(target=self.DB.join, args=messege[1])
            thread.run()
        if instruction[0]=='SYNCRONIZE':
            answer=f'{self.DB.time}\1{self.DB.get_logs(int(instruction[1]))}\1{self.S_COPY.time}\1{self.S_COPY.get_logs(int(instruction[2]))}'
        if instruction[0]=='UPDATE_TIME':
            if instruction[1]=='1':
                logs=ast.literal_eval(instruction[3])
                for log in logs:
                    self.DB.edit_database(log)
                self.DB.time=time
            else:
                logs=ast.literal_eval(instruction[3])
                for log in logs:
                    self.SS.edit_database(log)
                self.SS.time=time
        if instruction[0]=='RECOVER_MIDDLE_2':
            self.DB.join(messege[1])
            self.DB.join(messege[2])
            with self.lock:
                answer=str(self.DB)+'\1'+str(self.S_COPY)
                
        else:
            answer=self.DB.edit_database(messege)
        sock.sendto(answer.encode(), addr)

    def get_reference_node(self):
        #using cache nodes
        for ip in default_ip:
            ALIVE=self.connect(f'ALIVE',ip)
            if ALIVE!=None:
                return ip
        #using multicast
        ip=self.mcast_messege('DISCOVER')       
        return ip
    
    def get_sucessor_for_data(self,data_id):
        _id=hash(self.IP)
        if self.IP==self.SUCCESSOR:
            return self.IP
        with self.lock:
            successor=self.SUCCESSOR
        if _id==data_id:
            answer=self.IP
        elif _id<data_id and data_id<=hash(successor):
            answer=successor
        elif _id<data_id and data_id>hash(successor) and _id>hash(successor):
            answer=successor
        else:
            prev=self.FINGER_TABLE[0]
            for i in self.FINGER_TABLE[1:]:
                if hash(i)==data_id:
                    answer=i
                if hash[i]>data_id and hash[i]>hash(prev):
                    answer=self.connect(F'GET_SUCESSOR\1{data_id}',prev)
                if hash[prev]<data_id and hash(prev)>hash(i):
                    answer=self.connect(F'GET_SUCESSOR\1{data_id}',prev)
                prev=i
        if answer=='':
            return self.connect(F'GET_SUCESSOR\1{data_id}',self.FINGER_TABLE[-1])
        return answer

    def get_sucessors(self, base_ip=None):
        '''
            Gets the sucessors for my ip
        '''
        sucessors=[self.IP]
        i=0
        ip=base_ip
        while len(sucessors)!=5:
            if ip==None:#No reference node
                ip=self.get_reference_node()
                if ip==None:#No nodes
                    sucessors=[self.IP]*5
                continue
            s=self.connect(f'GET_SUCESSOR{sucessors[i]}',ip)
            if s==None:#reference node disconected
                if i==0:
                    ip=None
                    continue
                i-=1
                sucessors.pop()
                ip=sucessors[-1]
            sucessors.append(s)
            ip=s
            i+=1
        self.SUCCESSOR=sucessors[1]
        self.SS=sucessors[2]
        self.SSS=sucessors[3]

    def get_finger_table(self):
        self.FINGER_TABLE[0]=self.SUCCESSOR
        _id=hash(self.IP)
        i=1
        while i<160:
            data=(_id + 2 ** i) % (2 ** 160)
            ip=self.connect(f'GET_SUCCESSOR\1{data}',self.FINGER_TABLE_RIGHT[i-1])
            if ip==None and i!=1:
                i-=1
                continue
            elif ip==None:
                self.get_sucessors(self.SS)
                if self.SUCCESSOR==self.IP:
                    self.FINGER_TABLE[0]=self.IP
                    break
                continue
            self.FINGER_TABLE_RIGHT[i] = ip
            i+=1

    def update_finger_table(self):
        while True:
            if self.SUCCESSOR==self.IP:
                continue
            with self.lock:
                self.FINGER_TABLE[0]=self.SUCCESSOR
            _id=hash(self.IP)
            i=1
            while i<160:
                data=(_id + 2 ** i) % (2 ** 160)
                with self.lock:
                    previus_ip=self.FINGER_TABLE_RIGHT[i-1]
                ip=self.connect(f'GET_SUCCESSOR\1{data}',previus_ip)
                if ip==None and i!=1:
                    i-=1
                    continue
                elif ip==None:
                    continue
                with self.lock:
                    self.FINGER_TABLE_RIGHT[i] = ip
                i+=1

    def migrate(self):
        while True:
            succesor_db=self.connect("MIGRATE",self.SUCCESSOR)
            
            if succesor_db==None:
                self.get_sucessors(self.SS)
                if self.SUCCESSOR==self.IP:
                    return
                continue
            
            break
        succesor_db=succesor_db.split('\1')
        self.DB, self.S_COPY=parseDB(succesor_db[0]).split(hash(self.IP))
        self.SS_COPY=parseDB(succesor_db[1])
        self.connect(f"FORGET\1{self.IP}",self.SUCCESSOR)

    def check_copies(self):
        while True:
            sucessor_alive=self.update_copies()
            
            if sucessor_alive:
                sucessors=self.connect('SUCESSORS',self.SUCCESSOR)
                if sucessors==None:
                    continue
                sucessors=sucessors.split('\1')
                self.SS=sucessors[0]
                self.SSS=sucessors[1]
                continue
            
            sss=self.connect('RECOVER_MIDDLE',str(self.S_COPY))
            if sss!=None:
                self.SUCCESSOR=self.SS
                self.SS=self.SSS
                self.S_COPY.join(self.SS_COPY,False)
                self.SS_COPY=parseDB(sss)
                sucessors=self.connect('SUCESSORS',self.SUCCESSOR)
                if sucessors==None:
                    continue
                sucessors=sucessors.split('\1')
                self.SS=sucessors[0]
                self.SSS=sucessors[1]
                continue

            sss=self.connect('RECOVER_MIDDLE_2',str(self.S_COPY)+'\1'+str(self.SS_COPY))
            data=sss.split('\1')
            self.S_COPY=data[0]
            self.SS_COPY=data[1]
            self.SUCCESSOR=self.SSS
            sucessors=self.connect('SUCESSORS',self.SUCCESSOR)
            sucessors=sucessors.split('\1')
            self.SS=sucessors[0]
            self.SSS=sucessors[1]

    def update_copies(self):
        s_state=self.connect(f'SYNCRONIZE\1{self.S_COPY.time}\1{self.SS_COPY.time}', self.SUCCESSOR)
        if s_state==None:
            return None
        s_state=s_state.split('\1')
        t1=threading.Thread(target=self.syncronize, args=(s_state[0], s_state[1],self.S_COPY))
        t2=threading.Thread(target=self.syncronize, args=(s_state[2], s_state[3],self.SS_COPY, False))
        t1.run()
        t2.run()
        t1.join()
        t2.join()

    def syncronize(self, time, logs,db, ss):
        if time==db.time:
            return
        if time>db.time:
            for log in logs:
                db.edit_database(log)
            db.time=time
            return
        self.connect(f'{'UPDATE_TIME'}\1{2 if ss else 1}\1{db.get_logs(time)}',self.SUCCESSOR)