import socket
import struct
import threading
import ast
from DB import DB, parseDB
from DB_utils import *
import time
default_ip=['172.17.0.2']

'''
Crear funcion para encontrar successor y antecesor
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

        # Gets the information about the successors
        # -----------------------------------------
        self.SUCCESSOR=None
        self.SS=None
        self.SSS=None
        self.get_successors()

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
        #self.DB.add_client(self.IP,self.IP,self.IP)

        #Running the server and the heartbeats
        #-------------------------------------
        db_print=threading.Thread(target=self.db_print)
        db_print.start()
        hearbeat_thread=threading.Thread(target=self.heartbeats)
        hearbeat_thread.start()
        check_copies_thread=threading.Thread(target=self.check_copies)
        check_copies_thread.start()
        upd_ft_thread=threading.Thread(target=self.update_finger_table)
        upd_ft_thread.start()
        self.run()

    def db_print(self):
        while True:
            input()
            print("DB")
            print(self.DB)
            print("S_COPY")
            print(self.S_COPY)
            print("SS_COPY")
            print(self.SS_COPY)

    def heartbeats(self):
        while True:
            self.mcast_messege('ALIVE')
            time.sleep(5)

    def mcast_messege(self,messege):
        '''
            Try to discover other nodes via multicast. Return false if nobody answer
        '''
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        #sock.sendto(messege.encode(), (self.MCAST_GRP, self.MCAST_PORT))
        send_message(sock, messege.encode(), (self.MCAST_GRP, self.MCAST_PORT))
        # Esperar respuesta del servidor
        sock.settimeout(5)
        try:
            #data, _ = sock.recvfrom(1024)
            data, _ = receive_message(sock)
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
        #sock.sendto(messege.encode(), (ip, self.PORT))        
        send_message(sock, messege.encode(), (ip, self.PORT))    
        # Esperar respuesta        
        sock.settimeout(5)
        try:
            #data, _ = sock.recvfrom(1024)
            data, _ = receive_message(sock)
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

        for data, addr in receive_multiple_messages(sock):
        #while True:
            #data, addr = sock.recvfrom(1024)
            #data, addr = receive_message(sock)
            data=data.decode()
            if addr[0]==self.IP:
                continue
            if data=='ALIVE':
                ip=addr[0]
                if ip>self.IP and ip<self.SUCCESSOR or (self.IP>=self.SUCCESSOR and self.IP<ip) or (self.IP>=self.SUCCESSOR and self.SUCCESSOR>ip) or self.IP==self.SUCCESSOR:
                    self.SUCCESSOR=ip
                    print(f'Sucesor descubierto en ip {self.SUCCESSOR}')
            # Enviar respuesta
            #sock.sendto(self.IP.encode(), addr)
            send_message(sock, self.IP.encode(), addr)
    
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
        
        for data, addr in receive_multiple_messages(sock):
        #while True:
            #data, addr = sock.recvfrom(1024)
            #data, addr = receive_message(sock)
            
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
            answer=self.get_successor_for_data(hash(instruction[1]))   
        elif instruction[0]=='SUCCESSORS':
            answer=self.SUCCESSOR+'\1'+self.SS
        elif instruction[0]=='MIGRATE':
            with self.lock:
                answer=str(self.DB)+'\1'+str(self.S_COPY)
        elif instruction[0]=='RECOVER_MIDDLE':
            with self.lock:
                answer=str(self.S_COPY)
            thread=threading.Thread(target=self.DB.join, args=(instruction[1],True))
            thread.start()
        elif instruction[0]=='RECOVER_MIDDLE_2':
            self.DB.join(instruction[1],True)
            self.DB.join(instruction[2],True)
            with self.lock:
                answer=str(self.DB)+'\1'+str(self.S_COPY)
                
        elif instruction[0]=='SYNCRONIZE':
            answer=f'{self.DB.time}\1{self.DB.get_logs(int(instruction[1]))}\1{self.S_COPY.time}\1{self.S_COPY.get_logs(int(instruction[2]))}'
        elif instruction[0]=='UPDATE_TIME':
            if instruction[1]=='1':
                logs=ast.literal_eval(instruction[3])
                for log in logs:
                    self.DB.edit_database(log)
                self.DB.time=int(instruction[2])
            else:
                logs=ast.literal_eval(instruction[3])
                for log in logs:
                    self.SS_COPY.edit_database(log)
                self.SS_COPY.time=int(instruction[2])
            answer=''
        elif instruction[0]=='ALIVE':
            answer='True'
        else:
            print(f"Entro a la database: {instruction}")
            answer=self.DB.edit_database(messege)
        #sock.sendto(answer.encode(), addr)

        if messege=='':
            print("Mensaje vacio recibido")
        send_message(sock, answer.encode(), addr)

    def get_reference_node(self):
        #using cache nodes
        for ip in default_ip:
            ALIVE=self.connect(f'ALIVE',ip)
            if ALIVE!=None:
                return ip
        #using multicast
        ip=self.mcast_messege('DISCOVER')       
        return ip
    
    def get_successor_for_data(self,data_id):
        if self.IP==self.SUCCESSOR:
            return self.IP
        _id=hash(self.IP)
        answer=''
        if self.IP==self.SUCCESSOR:
            return self.IP
        with self.lock:
            successor=self.SUCCESSOR
        if _id==data_id:
            answer=self.IP
        elif _id<data_id and data_id<=hash(successor):
            answer=successor
        elif _id<data_id and data_id>=hash(successor) and _id>hash(successor):
            answer=successor
        else:
            prev=self.FINGER_TABLE[0]
            try_index=None
            for i in range(1,160):
                ip=self.FINGER_TABLE[i]
                if hash(ip)==data_id:
                    answer=ip
                    break
                if hash(ip)>data_id and hash(ip)>hash(prev):
                    answer=self.connect(f'GET_SUCCESSOR\1{data_id}',prev)
                    if answer==None:
                        try_index=i
                    break
                if hash(prev)<data_id and hash(prev)>hash(ip):
                    answer=self.connect(f'GET_SUCCESSOR\1{data_id}',prev)
                    if answer==None:
                        try_index=i
                    break
                prev=ip
        if answer=='':
            answer= self.connect(f'GET_SUCCESSOR\1{data_id}',self.FINGER_TABLE[-1])
            if answer==None:
                try_index=160
        if answer!=None:
            return answer
        for i in range(try_index-1,-1,-1):
            answer= self.connect(f'GET_SUCCESSOR\1{data_id}',self.FINGER_TABLE[i])
            if answer!=None:
                return answer
        return self.IP

    def get_successors(self, base_ip=None):
        '''
            Gets the successors for my ip
        '''
        successors=[self.IP]
        i=0
        ip=base_ip
        while len(successors)!=5:
            if ip==None:#No reference node
                ip=self.get_reference_node()
                if ip==None:#No nodes
                    successors=[self.IP]*5
                continue
            s=self.connect(f'GET_SUCCESSOR\1{successors[i]}',ip)
            print("Respuesta al mensaje: ",f'GET_SUCCESSOR\1{successors[i]}',": ",s)
            if s==None:#reference node disconected
                if i==0:
                    ip=None
                    continue
                i-=1
                successors.pop()
                ip=successors[-1]
            print("Sucesor descubierto",s)
            successors.append(s)
            ip=s
            i+=1
        print("Sucesores: ", successors)
        self.SUCCESSOR=successors[1]
        self.SS=successors[2]
        self.SSS=successors[3]

    def get_finger_table(self):
        self.FINGER_TABLE[0]=self.SUCCESSOR
        _id=hash(self.IP)
        i=1
        while i<160:
            data=(_id + 2 ** i) % (2 ** 160)
            ip=self.connect(f'GET_SUCCESSOR\1{data}',self.FINGER_TABLE[i-1])
            if ip==None and i!=1:
                i-=1
                continue
            elif ip==None:
                self.get_successors(self.SS)
                if self.SUCCESSOR==self.IP:
                    self.FINGER_TABLE[0]=self.IP
                    break
                continue
            self.FINGER_TABLE[i] = ip
            i+=1

    def update_finger_table(self):
        while True:
            no_response=[]
            change=False
            with self.lock:
                self.FINGER_TABLE[0]=self.SUCCESSOR
            _id=hash(self.IP)
            i=1
            while i<160:
                data=(_id + 2 ** i) % (2 ** 160)
                with self.lock:
                    previus_ip=self.FINGER_TABLE[i-1]
                if previus_ip==self.IP or previus_ip in no_response:
                    i+=1
                    continue
                ip=self.connect(f'GET_SUCCESSOR\1{data}',previus_ip)
                if ip==None:
                    print(f"{previus_ip} no responde")
                    no_response.append(previus_ip)
                    i+=1
                    continue
                with self.lock:
                    if self.FINGER_TABLE[i] != ip:
                        change=True
                    self.FINGER_TABLE[i] = ip
                i+=1
            for j in range(0,160):
                if self.FINGER_TABLE[j] in no_response:
                    if j!=0:
                        self.FINGER_TABLE[j]=self.FINGER_TABLE[j-1]
                        continue
                    else:
                        x=self.FINGER_TABLE[0]
                        while x!=self.SUCCESSOR:
                            pass
            if change:
                print('La finger_table ha sido actualizada')

    def migrate(self):
        while True:
            successor_db=self.connect("MIGRATE",self.SUCCESSOR)
            if successor_db==None:
                self.get_successors(self.SS)
                if self.SUCCESSOR==self.IP:
                    return
                continue
            break
        successor_db=successor_db.split('\1')
        
        self.DB, self.S_COPY=parseDB(successor_db[0]).split(hash(self.IP), hash(self.SUCCESSOR))
        self.SS_COPY=parseDB(successor_db[1])
        self.connect(f"FORGET\1{self.IP}\1{self.SUCCESSOR}",self.SUCCESSOR)

    def check_copies(self):
        
        while True:
            while self.SUCCESSOR==self.IP:pass

            successor_alive=self.update_copies()
            
            if successor_alive:
                successors=self.connect('SUCCESSORS',self.SUCCESSOR)
                if successors==None:
                    continue
                successors=successors.split('\1')
                if self.SS!=successors[0]:
                    print(f'Actualizando sucesor del sucesor: {successors[0]}')
                self.SS=successors[0]
                if self.SSS!=successors[1]:
                    print(f'Actualizando sucesor del sucesor del sucesor: {successors[1]}')
                self.SSS=successors[1]
                continue

            print(f"El sucesor {self.SUCCESSOR} desaparecio")
            
            if self.SS==self.IP:
                print("Nuevo sucesor: ", self.IP)
                self.SUCCESSOR=self.IP
                print("Nuevo sucesor del sucesor: ", self.IP)
                self.SS=self.IP
                print("Nuevo sucesor del sucesor del sucesor: ", self.IP)
                self.SSS=self.IP
                self.DB.join(self.S_COPY, False)
                self.S_COPY=DB()
                self.SS_COPY=DB()
                continue

            sss=self.connect('RECOVER_MIDDLE\1'+str(self.S_COPY),self.SS)
            if sss!=None:
                self.SUCCESSOR=self.SS
                print("Nuevo sucesor: ", self.SUCCESSOR)
                self.SS=self.SSS
                self.S_COPY.join(self.SS_COPY,False)
                self.SS_COPY=parseDB(sss)
                successors=self.connect('SUCCESSORS',self.SUCCESSOR)
                if successors==None:
                    continue
                successors=successors.split('\1')
                self.SS=successors[0]
                self.SSS=successors[1]
                print("Nuevo sucesor del sucesor: ", self.SS)
                print("Nuevo sucesor del sucesor del sucesor: ", self.SSS)
                continue
            
            if self.IP==self.SSS:
                print("Nuevo sucesor: ", self.IP)
                print("Nuevo sucesor del sucesor: ", self.IP)
                print("Nuevo sucesor del sucesor del sucesor: ", self.IP)
                self.DB.join(self.S_COPY, False)
                self.DB.join(self.S_COPY, False)
                self.S_COPY=DB()
                self.SS_COPY=DB()
                self.SUCCESSOR=self.IP
                self.SS=self.IP
                self.SSS=self.IP
                

            sss=self.connect('RECOVER_MIDDLE_2\1'+str(self.S_COPY)+'\1'+str(self.SS_COPY),self.SSS)
            data=sss.split('\1')
            self.S_COPY=data[0]
            self.SS_COPY=data[1]
            self.SUCCESSOR=self.SSS
            print("Nuevo sucesor: ", self.SUCCESSOR)
            successors=self.connect('SUCCESSORS',self.SUCCESSOR)
            successors=successors.split('\1')
            self.SS=successors[0]
            self.SSS=successors[1]
            print("Nuevo sucesor del sucesor: ", self.SS)
            print("Nuevo sucesor del sucesor del sucesor: ", self.SSS)

    def update_copies(self):
        s_state=self.connect(f'SYNCRONIZE\1{self.S_COPY.time}\1{self.SS_COPY.time}', self.SUCCESSOR)
        if s_state==None:
            return None
        s_state=s_state.split('\1')
        t1=threading.Thread(target=self.syncronize, args=(int(s_state[0]), s_state[1],self.S_COPY, True))
        t2=threading.Thread(target=self.syncronize, args=(int(s_state[2]), s_state[3],self.SS_COPY, False))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        return True

    def syncronize(self, time, logs,db, ss):
        if time==db.time:
            return
        if time>db.time:
            for log in ast.literal_eval(logs):
                print("Haciendo log: ",log)
                db.edit_database(log)
            db.time=time
            return
        self.connect(f'UPDATE_TIME\1{2 if ss else 1}\1{db.time}\1{db.get_logs(time)}',self.SUCCESSOR)