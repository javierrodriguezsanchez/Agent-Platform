import json
from Client.Client_connection import Give_Agent

def Load():
    """
    Reads a list from a JSON file and returns it.

    Args:
    file_path (str): The path to the JSON file.

    Returns:
    list: The list stored in the JSON file, or an empty list if the file does not exist or is empty.
    """
    try:
        with open('Client/Save.json', 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return []
    except FileNotFoundError:
        return []
    

def Save(agent):
    Info=Give_Agent(agent)
    Info=(Info.description,Info.actions,Info.actions_description)
    try:
        with open('Client/Save.json', 'r') as f:
            data = json.load(f)
            if not agent in data:
                data[agent]=Info
            with open('Client/Save.json', 'w') as f:
                json.dump(data, f)
    except FileNotFoundError:
        with open('Client/Save.json', 'w') as f:
            json.dump({agent:Info}, f)

def Delete(agent):
    try:
        with open('Client/Save.json', 'r') as f:
            data = json.load(f)
            if agent in data:
                del data[agent]
            with open('Client/Save.json', 'w') as f:
                json.dump(data, f)
    except FileNotFoundError:
        with open('Client/Save.json', 'w') as f:
            json.dump(dict(), f)
