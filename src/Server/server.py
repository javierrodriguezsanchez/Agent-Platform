import socket
import struct
import threading
from server_utils import *
import ast

class server:
    def __init__(self,info):
        self.MCAST_GRP = info['MULTICAST GROUP'] 
        self.MCAST_PORT = info['MULTICAST PORT']
        self.PORT = info['PORT']
        self.AGENTS_PORT = info['AGENTS PORT']
        self.IP = socket.gethostbyname(socket.gethostname())
        self.DB_IP = sorted(info['DATABASE IP'], key=lambda x:hash(x))
        self.DB_GRP = info['DATABASE GROUP']
        self.DB_PORT = info['DATABASE PORT']
        self.DB_MCAST_PORT = info['DATABASE MULTICAST PORT']
        self.CACHE_LIMIT=info['CACHE LIMIT']


    #SERVER THREADS
    #--------------
    def run(self):
        '''
            Runs the three servers, the last two runs on they own threads
            One is for the client request,
            Other to be discoverable via multicast by clients,
            The last one is to listen the heartbeats from the db nodes
        '''
        #OPEN THE THREADS
        discover_db_thread=threading.Thread(target=self.discover_db)
        discover_db_thread.start()
        mcast_thread=threading.Thread(target=self.mcast_run)
        mcast_thread.start()

        #RUNS THE SERVER
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self.PORT))
        print("Servidor unicast esperando mensajes...")
        for data, addr in receive_multiple_messages(sock):
            print(f"Mensaje recibido de {addr}: {data.decode()}")
            # Crear un nuevo hilo para manejar la interacción del cliente
            client_thread = threading.Thread(target=self.handle_client, args=(data, addr, sock))
            client_thread.start()


    def discover_db(self):
        '''
            Multicast listening to the database.
            The server always has a list of the most sparced CACHE_LIMIT nodes of the database
        '''
        print(f"Descubriendo nodos de base de datos por puerto {self.DB_MCAST_PORT}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(('', self.DB_MCAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(self.DB_GRP), socket.INADDR_ANY)

        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while True:
            data, addr = sock.recvfrom(1024)
            data=data.decode()
            if data=='ALIVE':
                ip=addr[0]
                if ip in self.DB_IP:
                    continue
                key=hash(ip)
                pos=get_successor([hash(x) for x in self.DB_IP],key)
                self.DB_IP.insert(pos,ip)
                while len(self.DB_IP)>self.CACHE_LIMIT:
                    out_index=smallest_difference_index([hash(x) for x in self.DB_IP])
                    self.DB_IP.pop(out_index)


    def mcast_run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(('', self.MCAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)

        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        print("Servidor multicast esperando mensajes...")
        while True:
            _, addr = sock.recvfrom(1024)
            # Enviar respuesta
            sock.sendto(f'SUCCESS\1{self.IP}'.encode(), addr)


    #HANDLE CLIENT
    #-------------
    def handle_client(self, data, addr, sock):
        success=True
        response=''
        messege=data.decode().split('\1')
        stop_event = threading.Event()
        wait_thread = threading.Thread(target=self.wait, args=(addr, sock, stop_event))
        wait_thread.start()
        
        #DIFFER CASE AND CREATE ANSWER
        if messege[0]=='SUBSCRIBE':
            result =self.connect_database(f"INSERT_CLIENT\1{messege[1]}\1{addr[0]}", messege[1])
            decoded_result = result.decode()
            success= (decoded_result=='True')
            response='' if success else 'El nombre ya existe'
        elif messege[0]=='QUERY':
            response=self.search_agents(messege[1])
        elif messege[0]=='CREATE':
            response, success = self.create_agent(messege[1],messege[2],addr[0])
        elif messege[0]=='UPDATE':
            response, success = self.update_agent(messege[1], messege[2], addr[0])
        elif messege[0]=='DELETE':
            response, success = self.delete_agent(messege[1])
        elif messege[0]=='EXEC':
            response, success = self.exec_action(messege[1],messege[2],messege[3])
        else:
            response='Protocolo incorrecto'
            success=False

        # SEND ANSWER
        stop_event.set()
        wait_thread.join()
        print(f'Enviando {response} a {addr}')
        result='SUCCESS' if success else 'ERROR'
        send_message(sock, f'{result}\1{response}'.encode(), addr)


    def wait(self, addr, sock, stop_event):
        try:
            while not stop_event.is_set():
                sock.sendto(b"\6", addr)
        except:
            pass


    #ACTIONS
    #-------
    def search_agents(self,query):
        #GET RELEVANT AGENTS FOR QUERY
        relevant_results=self.connect_database(f'GET_AGENTS\1{query}', query)
        if relevant_results==None:
            return []
        #GET INFO FOR AGENTS
        relevant_results=ast.literal_eval(relevant_results.decode())
        final_results=[]
        for agent in relevant_results:
            result=self.connect_database(f"GET_INFO_FOR_AGENT\1{agent}", agent)
            if result!=None and result.decode()!='DISCONNECTED':
                final_results.append(ast.literal_eval(result.decode()))
        return final_results


    def create_agent(self, name, info, ip):
        #ADD THE AGENT TO THE CATEGORY INFO
        agent_info=ast.literal_eval(info)
        #print(f"--------------{agent_info}-----------")
        actions=agent_info['actions']
        for action in actions:
            a=self.connect_database(f"NEW_AGENT_TO_ACTION\1{action}\1{name}", action)
            if a==None:
                return ('Error de conexion con la base de datos' , False)
        
        #ADD THE AGENT TO DATABASE
        a=self.connect_database(f"ADD_AGENT\1{name}\1{info}\1{ip}",name)
        if a==None:
            return ('Error de conexion con la base de datos' , False)
        return ('',True)


    def update_agent(self, name, info, ip):
        #UPDATE THE AGENT INFO
        actual_actions=agent_info['actions']
        #CHECKING CATEGORY CHANGE
        agent_info=ast.parse(info)
        past_actions=self.connect_database(f"UPDATE_AGENT\1{name}\1{info}\1{ip}", name)
        if past_actions==None:
            return ('Error de conexion con la base de datos' , False)
        past_actions=ast.literal_eval(past_actions.decode())
        #ADDING NEW CATEGORIES
        for new_action in [x for x in actual_actions if x not in past_actions]:
            a=self.connect_database(f"NEW_AGENT_TO_ACTION\1{new_action}\1{name}", new_action)
            if a==None:
                return ('Error de conexion con la base de datos' , False)
        #REMOVING OLD CATEGORIES
        for old_action in [x for x in past_actions if x not in actual_actions]:
            a=self.connect_database(f"REMOVE_AGENT_TO_ACTION\1{old_action}\1{name}", old_action)
            if a==None:
                return ('Error de conexion con la base de datos' , False)
        return ('',True)


    def delete_agent(self, name):
        #REMOVE THE AGENT INFO
        actions=self.connect_database(f"REMOVE_AGENT\1{name}", name)
        if actions==None:
            return  ('Error de conexion con la base de datos' , False)
        #REMOVE THE AGENTS IN CATEGORY
        for action in ast.literal_eval(actions.decode()):
            self.connect_database(f"REMOVE_AGENT_TO_ACTION\1{action}\1{name}", action)
        return ('',True)


    def exec_action(self,agent,action,args):
        #GET IP FROM DATABASE
        ip=self.connect_database(f"GET_IP_AGENT\1{agent}", agent)
        if ip==None:
            return ('Error de conexion con la base de datos' , False)
        ip = ip.decode()
        if ip=='False':
            return ('El agente no existe' , False)
        if ip=='DISCONNECTED':
            return ('El agente se encuentra fuera de linea' , False)
        
        # SEND ACTION EXECUTION TO THE AGENT
        messege=f'EXEC\1{agent}\1{action}\1{args}'
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        send_message(sock, messege.encode(), (ip, self.AGENTS_PORT))     
        
        # WAIT FOR ANSWER
        data = receive_message(sock)
        if data==None:
            self.connect_database(f"AGENT_DISCONNECTED\1{agent}", agent)
            return ('El agente se encuentra fuera de linea' , False)
        data=data.decode().split('\1')
        return (data[1], data[0]=='SUCCESS')

        
    #DATABASE CONNECTION
    #-------------------
    def connect_database(self,message, reference):
        '''
            Envia un mensaje a la database, si no encuentra database retorna none
        '''
        h_ref=hash(reference)
        # Crear socket unicast para comunicaciones futuras
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        while len(self.DB_IP)!=0:
            try:
                ip=self.DB_IP[get_successor([hash(x) for x in self.DB_IP], h_ref)-1]    
            except:
                print("EXPLOSION ",get_successor([hash(x) for x in self.DB_IP], h_ref))
                print(self.DB_IP)
                ip=self.DB_IP[0]
            right_node_ip=self.ask_successor_for_id(h_ref,ip)
            if right_node_ip==None:
                try:
                    self.DB_IP.remove(ip)
                except:
                    pass
                continue
            # Enviar mensajes al servidor usando la dirección unicast
            send_message(sock, message.encode(), (right_node_ip, self.DB_PORT))       
            # Esperar respuesta
            data = receive_message(sock)
            if data!=None:
                return data

        return None
    
    def ask_successor_for_id(self,id, initial_ip):
        '''
            Ask for the successor, skip messages chain
            If the ip is not connected, return None
        '''
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        path=[]
        ip=initial_ip
        while True:
            send_message(sock, f"SUCCESSOR\1{id}".encode(), (ip,self.DB_PORT))
            data = receive_message(sock)
            if data==None:
                if len(path)==0:#THE INITIAL IP DISCONNECTED
                    print(f"Error en comunicacion con {ip} en SUCCESSOR\1{id}")
                    return None
                ip=path.pop() #BACKTRACK TO PREVIOUS IP
                continue
            results=data.decode().split('\1')
            if results[0]=='FINAL': #FINAL ANSWER
                return results[1]
            path.append(ip) #PARCIAL ANSWER CASE, APPENDING TO THE PATH
            ip=results[1]
        