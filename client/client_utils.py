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
        module = importlib.import_module(f"Agents.{agent}.execute")
        
        info=dict()
        info['name']=f'{name}_{agent}'
        info['description']=module.Agent_Description()
        info['actions']=get_folders(f"Agents/{agent}/Actions")
        info['action description']={x:module.Action_Description(x) for x in info['actions']}
        return info
    except:
        return None

def excecute_agent_action(agent,action,args):
    try:
        module = importlib.import_module(f"Agents.{agent}.Actions.{action}.Run")
        return module.Run()
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