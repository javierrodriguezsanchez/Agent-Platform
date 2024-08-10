import os
import importlib
import json
import ast
import socket

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

def get_agent_instance(agent):
    my_module=importlib.import_module(f'Agents.{agent}.main')
    my_class = getattr(my_module, agent)
    return my_class()

def send_message(sock, message, addr):
    chunk_size = 1024
    sock.sendto(b"\6", addr)
    for i in range(0, len(message), chunk_size):
        chunk = message[i:i+chunk_size]
        sock.sendto(chunk, addr)
    sock.sendto(b"\7", addr)

def receive_message(sock):
    chunks = []
    sock.settimeout(10)
    while True:
        try:
            chunk, _ = sock.recvfrom(1024)
        except:
            return None
        if chunk == b"\7":
            break
        if chunk == b"\6":
            continue
        chunks.append(chunk)
    data = b''.join(chunks)
    return data

def receive_multiple_messages(sock):
    datas = {}
    while True:
        chunk, addr = sock.recvfrom(1024)

        if chunk == b"\6":
            datas[addr] = []
            continue

        if chunk == b"\7":
            data = b''.join(datas[addr])
            yield data, addr
            del datas[addr]

        elif addr in datas:
            datas[addr].append(chunk)
        else:
            datas[addr] = []
            datas[addr].append(chunk)