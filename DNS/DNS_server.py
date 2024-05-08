from DNS.DNS import DNS

dns=DNS()

def UpdateDNS():
    dns.Update()

def GetInfo():
    return (dns.get_agents(),dns.agent_actions)