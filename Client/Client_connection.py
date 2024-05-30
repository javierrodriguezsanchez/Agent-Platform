from DNS.DNS_server import GetInfo, exec

Agents=[]

def Search(query):
    global Agents
    Agents=GetInfo(query)
    return [a.name for a in Agents]

def GiveActionsForAgent(agent):
    return [a.actions for a in Agents if a.name==agent][0]

def Give_Agent(agent):
    return [a for a in Agents if a.name==agent][0]

def ExecuteAction(agent, action):
    exec(agent,action)