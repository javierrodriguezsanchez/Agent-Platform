import socket
import threading
import time
import struct
from DB_utils import *
from DB import database, parseDB

class DB_connection:
    def __init__(self, info):
        self.MCAST_GRP = info['MULTICAST GROUP'] 
        self.MCAST_PORT = info['MULTICAST PORT']
        self.PORT = info['PORT']
        self.CACHE_NODES=info['CACHE NODES']
        self.IP = socket.gethostbyname(socket.gethostname())
        
        
        self.SUCCESSOR=self.IP
        self.SS=self.IP #successor's successor ip
        self.SSS=self.IP #successor's successor's successor ip
        self.FINGER_TABLE=[self.IP]*160
        self.DB=database(hash(self.IP))

        self.CHORD_PROTOCOLS=[
            'MIGRATE_LEFT', 'SUCCESSOR', 'GIVE_SUCCESSORS', 'MIGRATE_RIGHT', 'SYNCRONIZE','ALIVE'
        ]

    def start(self):
        self.get_data()
        finger_table_thread=threading.Thread(target=self.update_finger_table)
        hearbeats_thread=threading.Thread(target=self.heartbeats)
        syncronize_thread=threading.Thread(target=self.syncronize)
        mcast_server_thread=threading.Thread(target=self.mcast_run)
        info_thread=threading.Thread(target=self.print_info)
        finger_table_thread.start()
        hearbeats_thread.start()
        info_thread.start()
        syncronize_thread.start()
        mcast_server_thread.start()
        self.run()


    #BASIC CONNECTION FUNCTIONS
    #--------------------------
    def ask(self,message,ip):
        '''
            Send the message to the ip and recieves the answer
            If the ip is not connected, return None
        '''
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        send_message(sock, message.encode(), (ip,self.PORT))
        data = receive_message(sock)
        if data!=None:
            return data.decode()
        print(f"Error en comunicacion con {ip}")
        return data


    def ask_successor_for_id(self,id, initial_ip):
        '''
            Ask for the successor, skip messages chain
            If the ip is not connected, return None
        '''
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        path=[]
        ip=initial_ip
        while True:
            send_message(sock, f"SUCCESSOR\1{id}".encode(), (ip,self.PORT))
            data = receive_message(sock)
            if data==None:
                if len(path)==0:#THE INITIAL IP DISCONNECTED
                    print(f"Error en comunicacion con {ip}")
                    return None
                ip=path.pop() #BACKTRACK TO PREVIOUS IP
                continue
            results=data.decode().split('\1')
            if results[0]=='FINAL': #FINAL ANSWER
                return results[1]
            path.append(ip) #PARCIAL ANSWER CASE, APPENDING TO THE PATH
            ip=results[1]
        

    def run(self):
        #RUNS THE SERVER
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self.PORT))
        print("Servidor unicast esperando mensajes...")
        for data, addr in receive_multiple_messages(sock):
            # Crear un nuevo hilo para manejar la interacción del cliente
            thread = threading.Thread(target=self.answer, args=(data, addr, sock))
            thread.start()


    #GET INFO ABOUT THE REST OF THE NODES
    #------------------------------------
    def get_data(self):
        while True:
            self.get_successors()
            if self.IP==self.SUCCESSOR:
                return
            db=self.ask(f'MIGRATE_LEFT\1{hash(self.IP)}',self.SUCCESSOR)
            if db!=None:
                self.DB=parseDB(db)
                self.DB.ID_LIST[0]=hash(self.IP)
                return


    def get_successors(self):
        #TRYS TO FIND THE SUCCESSORS BASED ON EXISTING IP
        def try_for_ip(ip): #RETURNS FALSE IF IP DISCONNECTED
            while True:
                successor=self.ask_successor_for_id(hash(self.IP),ip)
                if successor==None:
                    return False #NODE DOESNT EXIST
                other_successors=self.ask(f"GIVE_SUCCESSORS",successor)
                if other_successors==None:
                    continue #SUCCESSOR DISCONNECTED
                #SUCCESS
                aux=other_successors.split('\1')
                self.SUCCESSOR=successor
                self.SS=aux[0]
                self.SSS=aux[1]
                return True
        
        #TRYING WITH THE CACHE NODES
        for cache_ip in self.CACHE_NODES:
            if try_for_ip(cache_ip):
                return
        
        #TRYING VIA MULTICAST
        while True:
            ip=self.search_nodes()
            if ip==None:
                return
            if try_for_ip(ip):
                return


    def search_nodes(self):
        '''
            Use multicast to search the another nodes.
        '''
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        sock.sendto(b"DISCOVER", (self.MCAST_GRP, self.MCAST_PORT))
        sock.settimeout(5)
        try:
            _, addr = sock.recvfrom(1024)
            return addr[0]
        except socket.timeout:
            return None


    # MAIN THREADS
    # ------------
    def heartbeats(self):
        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.sendto('ALIVE'.encode(), (self.MCAST_GRP, self.MCAST_PORT))
            time.sleep(5)


    def print_info(self):
        while True:
            print()
            print("Nodo en ", self.IP)
            print(hash(self.IP))
            print("Sucesor: ",self.SUCCESSOR)
            print("Sucesor del sucesor: ",self.SS)
            print("Sucesor del sucesor del sucesor: ",self.SSS)
            print("DB")
            print(self.DB)
            print()
            a=input()
            if a == 'FT':
                print("FINGER TABLE")
                for x in range(len(self.FINGER_TABLE)):
                    print(f"{x+1}: {self.FINGER_TABLE[x]}")
                print()


    def mcast_run(self):
        print(f"Escuchando multicast por puerto {self.MCAST_PORT}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', self.MCAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while True:
            #listening
            data, addr = sock.recvfrom(1024)
            data=data.decode()
            if addr[0]==self.IP:
                continue
            if data=='ALIVE':
                ip=addr[0]
                if is_successor(self.IP, ip, self.SUCCESSOR):
                    print(f'Sucesor cambiado de {self.SUCCESSOR} a {ip}')
                    self.SUCCESSOR=ip
            # Answer
            sock.sendto(self.IP.encode(), addr)


    def update_finger_table(self):
        my_id=hash(self.IP)
        while True:
            while self.IP==self.SUCCESSOR: pass #no check if only node
            self.FINGER_TABLE[0]=self.SUCCESSOR
            previus_ip = self.SUCCESSOR
            next_ip=None

            #UPDATING ALL POSSITIONS
            for i in range(1,160):
                data=(my_id + 2 ** i) % (2 ** 160)
                next_ip=self.ask_successor_for_id(data, previus_ip)
                if next_ip==None:#The node disconnected
                    break
                self.FINGER_TABLE[i]=next_ip
                previus_ip=next_ip

            #CHECKING THE LAST NODE
            if next_ip!=None:
                alive=self.ask(f"ALIVE",next_ip)
                if alive!=None:
                    continue

            #REMOVING THE NODE DISCONNECTED
            if self.FINGER_TABLE[-1]==previus_ip:
                self.FINGER_TABLE[-1]=self.IP
            for i in range(158,-1,-1):
                if self.FINGER_TABLE[i]==previus_ip:
                    self.FINGER_TABLE[i]=self.FINGER_TABLE[i+1]


    def syncronize(self):
        '''
            Keeps successors list and copies update
        '''
        successor = self.SUCCESSOR
        sync_time = self.DB.time()

        while True:
            while self.SUCCESSOR == self.IP: pass

            # SUCCESSOR CHANGE
            if successor != self.SUCCESSOR:
                successor = self.SUCCESSOR        
                sync_time = self.DB.time()
                successor_alive = self.ask(f"MIGRATE_RIGHT\1{self.DB}",successor)!=None
                time.sleep(2)

            # SYNCRONIZE WITH SUCCESSOR
            else:
                aux = self.DB.time()
                logs = self.DB.give_logs(sync_time)
                sync_time = aux
                successor_alive = (self.ask(f"SYNCRONIZE\1{self.DB.id()}\1{logs}", successor) != None)
                if successor_alive:
                    self.DB.forget()

            # UPDATE SUCCESSORS' SUCCESSOR
            if successor_alive:
                following_successors = self.ask("GIVE_SUCCESSORS",successor)
                if following_successors != None:
                    following_successors = following_successors.split('\1')
                    self.SS = following_successors[0]
                    self.SSS = following_successors[1]
                    time.sleep(2)
                    continue


            #FIND NEW SUCCESSOR
            if successor!=self.SUCCESSOR:
                continue
            print(f"Sucesor {self.SUCCESSOR} desconectado. Actualizado a {self.SS}")
            self.SUCCESSOR=self.SS
            if self.IP!=self.SUCCESSOR:
                self.SS=self.SSS  
                self.SSS=self.IP
            else:
                self.DB.upd_id(str([hash(self.IP)]*4))
                self.SS=self.IP
                self.SSS=self.IP
        

    # CREATES RESPONSE TO MESSAGE
    # ---------------------------
    def answer(self,data,addr,sock):
        stop_event = threading.Event()
        wait_thread = threading.Thread(target=self.wait, args=(addr, sock, stop_event))
        wait_thread.start()
        instruction=data.decode().split('\1')[0]
        if instruction in self.CHORD_PROTOCOLS:
            response=self.chord_instruction(data.decode())
        else:
            response=self.DB.edit_database(data.decode())
        # SEND ANSWER
        stop_event.set()
        wait_thread.join()
        send_message(sock, response.encode(), addr)


    def wait(self, addr, sock, stop_event):
        try:
            while not stop_event.is_set():
                sock.sendto(b"\6", addr)
        except:
            pass


    def chord_instruction(self,message):
        instructions=message.split('\1')
        
        if instructions[0] == 'MIGRATE_LEFT':
            return str(self.DB)
        
        if instructions[0] == 'MIGRATE_RIGHT':
            new_data = self.DB.join(parseDB(instructions[1]))
            if new_data:
                def stabilize():
                    time.sleep(1)
                    self.ask(f'MIGRATE_RIGHT\1{self.DB}', self.SUCCESSOR)
                thread=threading.Thread(target=stabilize)
                thread.start()
            return ''
            
        if instructions[0] == 'SYNCRONIZE':
            self.DB.upd_id(instructions[1])
            self.DB.execute_logs(instructions[2])
            return ''
        
        if instructions[0] == 'GIVE_SUCCESSORS':
            return f'{self.SUCCESSOR}\1{self.SS}'
        
        if instructions[0] == 'SUCCESSOR':
            data_id=int(instructions[1])
            if is_successor(hash(self.IP),data_id,hash(self.SUCCESSOR)):
                return f"FINAL\1{self.SUCCESSOR}"
            behind=[x for x in self.FINGER_TABLE if hash(x)<=data_id]
            if behind==[]:
                behind=self.FINGER_TABLE
            ip = max(behind, key = lambda x:hash(x))
            return f"PARCIAL\1{ip}"
                
        return ''