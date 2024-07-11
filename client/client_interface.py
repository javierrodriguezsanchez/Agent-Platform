from client_connection import client
from client_utils import *

def run_interface(client_instance:client):
    
    option=0
    
    while option != 3:
        print("Bienvenido a la plataforma multiagente")
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
            search_interface(client_instance)

        if option==2:
            create_agent_interface(client_instance)

def search_interface(client_instance):

    print("Introduce tu criterio de busqueda o presiona ~~~ para volver atras:")
    query=input()
    if query=="~~~":
        return
    
    response=client_instance.search(query).split('\1')
    
    if response[0]=="ERROR":
        print(f"El siguiente error ha ocurrido: {response[1]}")
        input("Presiona enter para volver al menu principal")
        return
    
    response=decode_str(response[1])
    
    count=len(response)
    for i in range(count):
        agent=decode_str(response[i])
        print(f"{i+1}: {agent['name']}")
        print(f"\t{agent['description']}")
    print(f"Selecciona el numero del agente con el que desees interactuar o presiona {count+1} para volver atras")
    
    try:
        option=int(input())
    except:
        input("Opcion invalida, presiona enter para volver al menu principal")
        return
        
    if option>count+1 or option<1:
        input("Opcion invalida, presiona enter para volver al menu principal")
        return
    
    if option !=count+1:
        interact_interface(client_instance, response[option-1])

def interact_interface(client_instance, agent):
    '''
    '''
    #Show actions
    #Select actions
    #Si tiene argumentos elegir argumentos
    #Crear query
    #response=interact_interface(client_instance, option)
    #print(response)
    #input("Press enter to continue")

def create_agent_interface(client_instance):
    agents=get_folders('Agents/')
    
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
    
    response=client_instance.create_agent(agents[option-1]).split('\1')
    if response[0]=="ERROR":
        print(f"El siguiente error ha ocurrido: {response[1]}")
        input("Presiona enter para volver al menu principal")
        return
    
    print("El agente se ha creado correctamente")
    input("Presiona enter para volver al menu principal")