from client_utils import *

class client_interface:
    def __init__(self,connection):
        self.connection=connection
        self.client_name=load('name')

    def run_interface(self):
        self.login()
        self.update_agents_interface()
        option=0
        
        while option != 3:
            print(f"Bienvenido {self.client_name}")
            print("Seleccione una opcion")
            print("1- Buscar agentes disponibles")
            print("2- Crear tu propio agente")
            print("3- Salir de la plataforma")
            try:
                option=int(input())
            except:
                print("Opcion invalida, vuelva a intentarlo")
                continue
            
            if option>3 or option<1:
                print("Opcion invalida, vuelva a intentarlo")
            
            if option==1:
                self.search_interface()

            if option==2:
                self.create_agent_interface()

    def search_interface(self):

        print("Introduce tu criterio de busqueda o presiona ~~~ para volver atras:")
        query=input()
        if query=="~~~":
            return
        
        response=self.connection.search(query).split('\1')
        
        if response[0]=="ERROR":
            print(f"El siguiente error ha ocurrido: {response[1]}")
            input("Presiona enter para volver al menu principal")
            return
        
        response=decode_str(response[1])
        
        count=len(response)
        for i in range(count):
            agent=response[i]
            print(f"{i+1}: {agent['name']}")
            print(f"\t{agent['description']}")
        print(f"Selecciona el numero del agente con el que desees interactuar o presiona {count+1} para volver atras")
        
        try:
            option=int(input())
        except:
            input("Opcion invalida, presiona enter para volver al menu principal: ")
            return
            
        if option>count+1 or option<1:
            input("Opcion invalida, presiona enter para volver al menu principal: ")
            return
        
        if option !=count+1:
            self.interact_interface(response[option-1])

    def login(self):
        
        print("Bienvenido a la plataforma multiagente")
        
        while True:
            name=self.client_name
            if self.client_name==None:
                name=input("Introduce su nombre de usuario: ")
                if '\1' in name:
                    print("Nombre invalido. Intentelo de nuevo")
                    continue
            password=input('Introduzca su password: ')
            if '\1' in password:
                print("Password invalida. Intentelo de nuevo")
                continue
            response=self.connection.start(name,password,self.client_name==None).split('\1')
            if response[0]=='ERROR':
                print(f"El siguiente error ha ocurrido: {response[1]}")
                continue
            self.client_name = name
            save('name',self.client_name)
            return
    
    def interact_interface(self, agent):
        num_actions=len(agent['actions'])
        for i in range(num_actions):
            print(f"{i+1}: {agent['actions'][i]}")
            print(f"\t{agent['action description'][agent['actions'][i]]}")
        print(f"Selecciona el numero del agente con el que desees interactuar o presiona {num_actions+1} para volver atras")
        
        try:
            option=int(input())
        except:
            input("Opcion invalida, presiona enter para volver al menu principal: ")
            return
            
        if option>num_actions+1 or option<1:
            input("Opcion invalida, presiona enter para volver al menu principal: ")
            return
        
        if option ==num_actions+1:
            return
        
        print('Write the parameters')
        args=input()
        response=self.connection.interact(agent['name'],agent['actions'][option-1],args).split('\1')
        if response[0]=='ERROR':
            print(f"El siguiente error ha ocurrido: {response[1]}")
        print(response[1])
        input("Press enter to continue: ")

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

        print('Elige al agente que deseas subir a la plataforma:')
        for i in range(len(agents)):
            print(f"{i+1}- {agents[i]}")
        print(f'Escribe {len(agents)+1} para volver al menu principal')
        try:
            option=int(input())
        except:
            input("Opcion invalida, presiona enter para volver al menu principal")
            return
        if option>len(agents)+1 or option<1:
            input("Opcion invalida, presiona enter para volver al menu principal")
            return
        if option ==len(agents)+1:
            return
        
        response=self.connection.create_agent(self.client_name,agents[option-1]).split('\1')
        if response[0]=="ERROR":
            print(f"El siguiente error ha ocurrido: {response[1]}")
            input("Presiona enter para volver al menu principal")
            return
        
        print("El agente se ha creado correctamente")
        
        created_agents.append(agents[option-1])
        save('agents',created_agents)

        input("Presiona enter para volver al menu principal")