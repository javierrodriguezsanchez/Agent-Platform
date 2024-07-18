from client_utils import *

green = '\033[92m'
red = '\033[91m'
yellow = '\033[93m'
reset = '\033[0m'

class client_interface:
    def __init__(self,connection):
        self.connection=connection
        self.client_name=load('name')

    def run_interface(self):
        self.login()
        self.update_agents_interface()
        option=0
        
        while option != 3:
            print(green)
            print(f"Bienvenido {self.client_name}")
            print("---------------------------------")
            print()
            print("Seleccione una opción")
            print("[1] - Buscar agentes disponibles")
            print("[2] - Crear tu propio agente")
            print("[3] - Salir de la plataforma")
            print(reset)
            try:
                option=int(input())
            except:
                print(red)
                print("Opción inválida, vuelva a intentarlo")
                print(reset)
                continue
            
            if option>3 or option<1:
                print(red)
                print("Opción inválida, vuelva a intentarlo")
                print(reset)
            
            if option==1:
                self.search_interface()

            if option==2:
                self.create_agent_interface()

    def search_interface(self):

        print(green)
        print("Introduce tu criterio de búsqueda o escriba --- para volver atras:")
        print(reset)

        query=input()
        if query=="---":
            return
        
        response=self.connection.search(query).split('\1')
        
        if response[0]=="ERROR":
            print(red)
            print(f"El siguiente error ha ocurrido: {response[1]}")
            input(green + "Presiona enter para volver al menú principal")
            print(reset)
            return
        
        response=decode_str(response[1])
        
        count=len(response)
        print()
        for i in range(count):
            agent=response[i]
            print(green + f"[{i+1}] - {agent['name']}")
            print(yellow + f"\t{agent['description']}")
        print(green + f"Selecciona el número del agente con el que desees interactuar o presiona {count+1} para volver atrás")
        print(reset)
        
        try:
            option=int(input())
        except:
            print(red)
            input("Opción inválida, presiona enter para volver al menú principal: ")
            print(reset)
            return
            
        if option>count+1 or option<1:
            print(red)
            input("Opción inválida, presiona enter para volver al menú principal: ")
            print(reset)
            return
        
        if option !=count+1:
            self.interact_interface(response[option-1])

    def login(self):
        
        print(green)
        print("Bienvenido a la plataforma multiagente")
        print("--------------------------------------")
        print(reset)
        
        while True:
            print()
            name=self.client_name
            if self.client_name==None:
                name=input(green + "Introduzca su nombre de usuario: " + reset)
                if ('\1' or '\2' or '_') in name:
                    print(red + "Nombre inválido. Inténtelo de nuevo" + reset)
                    continue
            password=input(green + 'Introduzca su password: ' + reset)
            if ('\1' or '\2' or '_') in password:
                print(red + "Password inválido. Inténtelo de nuevo" + reset)
                continue
            response=self.connection.start(name,password,self.client_name==None).split('\1')
            if response[0]=='ERROR':
                print(red + f"El siguiente error ha ocurrido: {response[1]}" + reset)
                continue
            self.client_name = name
            save('name',self.client_name)
            return
    
    def interact_interface(self, agent):
        num_actions=len(agent['actions'])
        print()
        for i in range(num_actions):
            print(green + f"[{i+1}] - {agent['actions'][i]}")
            print(yellow + f"\t{agent['action description'][agent['actions'][i]]}")
        print(green + f"Selecciona el número de la funcionalidad del agente que deseas usar o presiona {num_actions+1} para volver atrás")
        print(reset)

        try:
            option=int(input())
        except:
            print(red)
            input("Opción inválida, presiona enter para volver al menú principal: ")
            print(reset)
            return
            
        if option>num_actions+1 or option<1:
            print(red)
            input("Opción inválida, presiona enter para volver al menú principal: ")
            print(reset)
            return
        
        if option ==num_actions+1:
            return
        
        print(green)
        print('Introduzca los parámetros')
        print(reset)

        args=input()
        response=self.connection.interact(agent['name'],agent['actions'][option-1],args).split('\1')
        if response[0]=='ERROR':
            print(red)
            print(f"El siguiente error ha ocurrido: {response[1]}")
            print(reset)
        print(response[1])
        input(green + "Press enter to continue: ")
        print(reset)

    def update_agents_interface(self):
        print("Reiniciando agentes...")
        logs=self.connection.update_agents(self.client_name)
        for log in logs:
            print(log)

    def create_agent_interface(self):
        agents=get_folders('Agents/')
        
        created_agents=load('agents')
        if created_agents==None:
            created_agents=[]

        agents=[x for x in agents if x not in created_agents]

        print(green)
        print('Elige al agente que deseas subir a la plataforma:')
        for i in range(len(agents)):
            print(f"[{i+1}] - {agents[i]}")
        print(f'Escribe {len(agents)+1} para volver al menú principal')
        print(reset)
        try:
            option=int(input())
        except:
            print(red)
            input("Opción inválida, presiona enter para volver al menú principal: ")
            print(reset)
            return
        if option>len(agents)+1 or option<1:
            print(red)
            input("Opción inválida, presiona enter para volver al menú principal: ")
            print(reset)
            return
        if option ==len(agents)+1:
            return
        
        response=self.connection.create_agent(self.client_name,agents[option-1]).split('\1')
        if response[0]=="ERROR":
            print()
            print(red + f"El siguiente error ha ocurrido: {response[1]}")
            input(green + "Presiona enter para volver al menú principal")
            print(reset)
            return
        
        print(green)
        print("El agente se ha creado correctamente")
        
        created_agents.append(agents[option-1])
        save('agents',created_agents)

        input("Presiona enter para volver al menú principal")
        print(reset)