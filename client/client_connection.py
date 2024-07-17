import socket
from client_utils import *
import threading

class client:
    def __init__(self, MCAST_GRP, MCAST_PORT, PORT, AGENT_PORT):
        #MULTICAST INFO
        self.MCAST_GRP=MCAST_GRP
        self.MCAST_PORT=MCAST_PORT
        
        # SERVER INFO
        self.PORT=PORT
        self.SERVER_IP=load('IP')
        if self.SERVER_IP==None:
            self.search_server()
        
        #AGENT SERVER INFO
        self.AGENTS_PORT=AGENT_PORT
        self.agents=dict()
        self.lock = threading.Lock()
        self.agent_server_thread = threading.Thread(target=self.run_agents)
        self.agent_server_thread.start()


    def search_server(self):
        '''
            Use multicast to search the server
        '''
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        print("Buscando servidor...")
        #sock.sendto(b"DISCOVER", (self.MCAST_GRP, self.MCAST_PORT))
        send_message(sock, b"DISCOVER", (self.MCAST_GRP, self.MCAST_PORT))
        # Esperar respuesta del servidor
        try:
            data, _ = receive_message(sock)
            self.SERVER_IP = data.decode().split('\1')[1]
            print(f"Servidor encontrado en {self.SERVER_IP}")
            save('IP',self.SERVER_IP)
        except socket.timeout:
            print("No se encontró ningún servidor")
            exit()

    def connect(self,message):
        # Crear socket unicast para comunicaciones futuras
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Enviar mensajes al servidor usando la dirección unicast
        #sock.sendto(message.encode(), (self.SERVER_IP, self.PORT))        
        send_message(sock, message.encode(), (self.SERVER_IP, self.PORT))   
        # Esperar respuesta
        
        sock.settimeout(5)
        try:
            data, _ = receive_message(sock)
            return data.decode()
        except socket.timeout:
            self.search_server()
            return self.connect(message)

    def update_agents(self,name):
        """
            This function is use when the client reconects to the server
        """
        agents=load('agents')
        if agents==None:
            return []
        to_remove=[]
        logs=[]
        for agent in agents:
            info=get_agent_info(name,agent)
            if info==None:
                logs.append(f"El agente {agent} dejo de existir o de cumplir con el formato deseado")
                response=self.connect(f'DELETE\1{name}_{agent}').split('\1')
                if response[0]=="ERROR":
                    logs.append(f"Error al eliminarlo de la plataforma: {response[1]}")
                    continue
                logs.append(f"El agente {response[1]} fue eliminado satisfactoriamente de la plataforma")
                to_remove.append(agent)
                continue
            
            response=self.connect(f"UPDATE\1{name}_{agent}\1{str(info)}").split('\1')
            if response[0]=='ERROR':
                logs.append(f"Error al actualizar el agente {agent} en la plataforma: {response[1]}")
                continue
            
            logs.append(f'Se ha actualizado satisfactoriamente la informacion del agente {agent} en la plataforma')
            self.agents[info['name']]=get_agent_instance(agent)

        save('agents',[x for x in agents if x not in to_remove])
        return logs
        
    #BASIC CLIENTS OPERATIONS
    #------------------------
    def start(self,name,password,SUBSCRIBE):
        action="SUBSCRIBE" if SUBSCRIBE else "LOGIN"
        return self.connect(f'{action}\1{name}\1{password}')
    
    def search(self,query):
        return self.connect(f"QUERY\1{query}")
    
    def interact(self,agent,action, args):
        return self.connect(f'EXEC\1{agent}\1{action}\1{str(args)}')

    def create_agent(self,name,agent):
        info=get_agent_info(name,agent)
        if info==None:
            return "ERROR\1El agente no tiene el formato deseado"
        
        response=self.connect(f"CREATE\1{info['name']}\1{str(info)}")
        decode_response=response.split('\1')
        if decode_response[0]=='ERROR':
           return response
        
        with self.lock:
            self.agents[info['name']]=get_agent_instance(agent)
        return response
    
    # LOCAL AGENTS SERVER
    #--------------------
    def run_agents(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self.AGENTS_PORT))
        print("Corriendo servidor de agentes por el puerto ", self.AGENTS_PORT)
        while True:
            data, addr = receive_message(sock)
            # Crear un nuevo hilo para manejar la interacción del cliente
            agent_thread = threading.Thread(target=self.handle_agent_call, args=(data, addr, sock))
            agent_thread.start()

    def handle_agent_call(self, data, addr,sock):
        request=data.decode().split('\1')
        if request[0]!='EXEC':
            sock.sendto('ERROR: Protocolo incorrecto'.encode(), addr)
            return
        with self.lock:
            response=getattr(self.agents[request[1]],request[2])(self.interact, decode_str(request[3]))
        if response==None:
            response='ERROR\1La accion no se pudo llevar a cabo'
        else:
            response=f'SUCESS\1{response}'
        sock.sendto(response.encode(), addr)