from client_connection import client

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
            create_interface(client_instance)

def search_interface(client_instance):
    print("Introduce tu criterio de busqueda o presiona ~~~ para volver atras:")
    query=input()
    if query=="~~~":
        return
    response=client_instance.connect(f"QUERY\1{query}").split('\1')
    if response[0]=="ERROR":
        print(f"El siguiente error ha ocurrido: {response[1]}")
    count=len(response)
    for i in range(count):
        print(f"{i+1}: {response[i]}")
    print(f"Selecciona el numero del agente con el que desees interactuar o presiona {count+1} para volver atras")
    
    try:
        option=int(input())
    except:
        print("Opcion invalida, volviendo a menu principal")
        return
        
    if option>count+1 or option<1:
        print("Opcion invalida, volviendo a menu principal")
    
    if option !=count+1:
        interact_interface(client_instance, response[option-1])

def interact_interface(client_instance, agent):
    pass

def create_interface(client_instance):
    pass