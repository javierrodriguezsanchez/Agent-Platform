import importlib
import os

class Agent:
    def __init__(self,name,description,actions,actions_description):
        self.name = name
        self.description = description
        self.actions = actions
        self.actions_description = actions_description

def search_agents():
    #Change for distributed
    agents = os.listdir(f"Agents")
    agents.pop()
    agents.pop()
    desc=dict()
    actions=dict()
    act_desc=dict()
    for a in agents:
        module = importlib.import_module(f"Agents.{a}.execute")
        desc[a]= module.Agent_Description()
        actions[a] = os.listdir(f"Agents/{a}/Actions")
        
        #TODO: EDITAR ESTA PARTE
        module = importlib.import_module(f"Agents.{a}.execute")
        act_desc[a]=dict()
        for aa in actions[a]:
            act_desc[a][aa] = module.Agent_Description()
    
    return [Agent(a,desc[a],actions[a],act_desc[a]) for a in agents]

agents=search_agents()


def GetInfo(query): 
    #NOTE: CHANGE BY SRI
    return agents

def exec(agent,action):
    module = importlib.import_module(f"Agents.{agent}.execute")
    module.Execute_Action(action)