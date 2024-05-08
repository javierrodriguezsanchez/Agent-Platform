from DNS.DNS import DNS

dns=DNS()

def UpdateDNS():
    dns.Update()

def Agents_Info():
    return [(x,dns.agent_actions(x)) for x in dns.get_agents()]