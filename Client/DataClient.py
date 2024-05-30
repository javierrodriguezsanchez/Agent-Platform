import json
from Client.Client_connection import Give_Agent

class Agent:
    def __init__(self,name,description,actions,actions_description):
        self.name = name
        self.description = description
        self.actions = actions
        self.actions_description = actions_description


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
            return [Agent(x,data[x][0],data[x][1],data[x][2]) for x in data]
    except FileNotFoundError:
        return []
    

def Save(agent):
    Info=(agent.description,agent.actions,agent.actions_description)
    try:
        with open('Client/Save.json', 'r') as f:
            data = json.load(f)
            if not agent.name in data:
                data[agent.name]=Info
            with open('Client/Save.json', 'w') as f:
                json.dump(data, f)
    except FileNotFoundError:
        with open('Client/Save.json', 'w') as f:
            json.dump({agent.name:Info}, f)

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
