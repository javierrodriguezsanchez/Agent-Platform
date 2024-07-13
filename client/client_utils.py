import os
import importlib
import json
import ast

def get_folders(ruta):
    try:
        # Obtener una lista de todos los elementos en la ruta especificada
        elementos = os.listdir(ruta)
        
        # Filtrar solo las carpetas
        carpetas = [elemento for elemento in elementos if os.path.isdir(os.path.join(ruta, elemento))]
        
        return carpetas
    except FileNotFoundError:
        print(f"Error: La ruta '{ruta}' no existe.")
        return []
    except PermissionError:
        print(f"Error: No tienes permisos para acceder a la ruta '{ruta}'.")
        return []
    
def get_agent_info(name,agent):
    try:
        module = importlib.import_module(f"Agents.{agent}.main")
        info=module.get_info()
        info['name']=name+'_'+agent
        return info
    except:
        return None

def excecute_agent_action(agent,action,args):
    try:
        args=decode_str(args)

        # Importar la biblioteca de forma dinámica
        my_module = importlib.import_module(f'Agents.{agent}.main')

        # Crear un objeto de la clase MyClass
        my_class = getattr(my_module, agent)
        my_object = my_class()
        return getattr(my_object, action)(args)
    except:
        return None

def decode_str(data):
    return ast.literal_eval(data)

def load(x):
    try:
        with open(os.path.join('data.json')) as f:
            data = json.load(f)
    except:
        # Crear un nuevo diccionario vacío
        data = {}
        # Crear el archivo JSON con el diccionario vacío
        with open('data.json', 'w') as archivo:
            json.dump(data, archivo)
    
    if x not in data.keys():
        return None
    
    return data[x]

def save(field,content):
    try:
        with open(os.path.join('data.json')) as f:
            data = json.load(f)
    except:
        # Crear un nuevo diccionario vacío
        data = {}
        # Crear el archivo JSON con el diccionario vacío
        with open('data.json', 'w') as archivo:
            json.dump(data, archivo)
    data[field]=content
    # Crear el archivo JSON con el diccionario vacío
    with open('data.json', 'w') as archivo:
        json.dump(data, archivo)