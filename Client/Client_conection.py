from DNS.DNS_server import GetInfo
import importlib

def AskDNS():
    return GetInfo()

def saveInfo(Agents,Actions):
    pass
def loadInfo(Agents,Actions):
    pass

Agents, Actions = AskDNS()
saveInfo(Agents,Actions)

def GiveAgents():
    return Agents

def GiveActionsForAgent(agent):
    return Actions[agent]

def ExcecuteAction(agent, action):
    module = importlib.import_module(f"Agents.{agent}.execute")
    module.Execute_Action(action)