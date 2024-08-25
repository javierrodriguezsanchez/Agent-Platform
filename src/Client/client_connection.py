import socket
from client_utils import *
import threading

class connection:
    def __init__(self,info):
        #GENERAL INFO ABOUT SERVERS
        self.SERVER_PORT = info['SERVER PORT']
        self.SERVER_MCAST_PORT = info['SERVER MULTICAST PORT']
        self.SERVER_GRP = info['SERVER GROUP']
        
        #POSIBLE SERVER IP
        ip=load('IP')
        ip=ip if ip != None else []
        new_ip=[x for x in info['SERVER IP'] if x not in ip]
        self.SERVER_IP=ip+new_ip
        if new_ip != []:
            save('IP',self.SERVER_IP)
        self.ip_index=0
        if self.SERVER_IP == []:
            ip = self.search_server()
            if ip==None:
                print("No se encontro ningun server")
                return 'ERROR\1No se pudo encontrar servidor'
            else:
                self.SERVER_IP.append(ip)

        #AGENT SERVER INFO
        self.AGENTS_PORT=info['AGENT PORT']
        self.AGENTS=dict()
        self.agent_server_thread = threading.Thread(target=self.run_agents)
        self.agent_server_thread.start()
    

    #BASIC CLIENT CONNECTION
    #-----------------------
    def send_message(self, message):
        '''
            Send a message to a server and return the response. If server doesnt answer:
            - Try the next direction saved in cache
            - If there isnt more directions in cache, search a new server
            - If the server is new, save the server in cache
            - If no server is discovered, return None
        '''
        # Crear socket unicast para comunicaciones futuras
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        coded_message = message.encode()

        while True:
            # Enviar mensajes al servidor usando la dirección unicast
            addr=(self.SERVER_IP[self.ip_index], self.SERVER_PORT)
            send_message(sock, coded_message, addr)
            
            # Esperar respuesta
            data = receive_message(sock)
            if data!=None:
                return data.decode()
            
            print("El server ",addr," se desconecto")
            self.ip_index+=1
            if self.ip_index!=len(self.SERVER_IP):
                continue #Probando default servers
            ip=self.search_server() #Buscar nuevo server
            if ip==None:
                print("No se encontro ningun server")
                return 'ERROR\1No se pudo encontrar servidor'
            if ip in self.SERVER_IP:
                self.ip_index=self.SERVER_IP.index(ip)
                continue
            self.SERVER_IP.append(ip)
            save('IP',self.SERVER_IP)

    def search_server(self):
        '''
            Use multicast to search the server. If no server, search by  broadcast a DNS to give a server
        '''
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        print("Buscando servidor...")
        sock.sendto(b"DISCOVER", (self.SERVER_GRP, self.SERVER_MCAST_PORT))
        # Esperar respuesta del servidor
        try:
            data, addr = sock.recvfrom(1024)
            return addr[0]
        except socket.timeout:
            return self.ask_DNS()
        
    def ask_DNS(self): #TODO IMPLEMENT
        return None
    

    #SERVER INTERACTIONS
    #-------------------
    def update_agents(self,name):
        """
            This function is use when the client reconects to the platform
        """
        #GET AGENTS
        agents=load('agents')
        if agents==None:
            return
        
        to_remove=[]
        for agent in agents:
            info=get_agent_info(name,agent)
            
            #REMOVING THOSE WHO DOESNT HAVE THE CONDITIONS
            if info==None:
                print(f"El agente {agent} dejo de existir o de cumplir con el formato deseado")
                response=self.send_message(f'DELETE\1{name}_{agent}').split('\1')
                if response[0]=="ERROR":
                    print(f"Error al eliminarlo de la plataforma: {response[1]}")
                    continue
                print(f"El agente {response[1]} fue eliminado satisfactoriamente de la plataforma")
                to_remove.append(agent)
                continue
            
            #UPDATING THE INFO
            response=self.send_message(f"UPDATE\1{name}_{agent}\1{str(info)}").split('\1')
            if response[0]=='ERROR':
                print(f"Error al actualizar el agente {agent} en la plataforma: {response[1]}")
                continue
            print(f'Se ha actualizado satisfactoriamente la informacion del agente {agent} en la plataforma')
            self.AGENTS[info['name']]=get_agent_instance(agent)

        save('agents',[x for x in agents if x not in to_remove])
        return
    
    def subscribe(self,name):
        return self.send_message(f'SUBSCRIBE\1{name}')
    
    def search(self,query):
        return self.send_message(f'QUERY\1{query}')
    
    def exec(self,agent,action, args): #TODO: DIFFER LOCAL VS GLOBAL
        return self.send_message(f'EXEC\1{agent}\1{action}\1{str(args)}')

    def create_agent(self,name,agent):
        info=get_agent_info(name,agent)
        if info==None:
            return "ERROR\1El agente no tiene el formato deseado"
        
        response=self.send_message(f"CREATE\1{info['name']}\1{str(info)}")
        decode_response=response.split('\1')
        if decode_response[0]=='ERROR':
           return response
        
        #with self.lock:
        self.AGENTS[info['name']]=get_agent_instance(agent)
        return response
    

    # LOCAL AGENTS SERVER
    #--------------------
    def run_agents(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self.AGENTS_PORT))
        print("Corriendo servidor de agentes por el puerto ", self.AGENTS_PORT)
        for data, addr in receive_multiple_messages(sock):
            # Crear un nuevo hilo para manejar la interacción del cliente
            agent_thread = threading.Thread(target=self.handle_agent_call, args=(data, addr, sock))
            agent_thread.start()

    def handle_agent_call(self, data, addr,sock):
        #CHECK THE FORMAT
        request=data.decode().split('\1')
        if request[0]!='EXEC':
            send_message(sock, 'ERROR\1Protocolo incorrecto'.encode(), addr)
            return
        
        #RETURN WAIT MESSAGES, USEFULL TO DIFFER THE CASE OF LATE RESPONSE AND DISCONNECTION 
        stop_event = threading.Event()
        wait_thread = threading.Thread(target=self.wait, args=(addr, sock, stop_event))
        wait_thread.start()

        #GET THE RESPONSE
        #with self.lock:
        if request[1] in self.AGENTS:
            action=getattr(self.AGENTS[request[1]],request[2])
            response=action(self.search, self.exec, decode_str(request[3]))
            if response==None:
                response='ERROR\1La accion no se pudo llevar a cabo'
            else:
                response=f'SUCCESS\1{response}'
        else:
            response='ERROR\1La accion no se pudo llevar a cabo'

        #STOP THE WAITING AND ANSWER THE CLIENT
        stop_event.set()
        wait_thread.join()
        send_message(sock, response.encode(), addr)

    def wait(self, addr, sock, stop_event):
        try:
            while not stop_event.is_set():
                sock.sendto(b"\6", addr)
        except:
            pass