import ast
    
class DB:
    def __init__(self):
        self.clients=dict()
        self.agents=dict()
    def add_client(self,name,password,ip):
        self.clients[name]=(password,ip)
    def add_agent(self,name,dic,ip):
        self.agents[name]=(ast.literal_eval(dic),ip)
    def check_password(self, name, password):
        return self.clients[name]==password
    def get_ip_agent(self,name):
        return self.agents[name][1]
    def get_agents(self,query):
        return [x for x,_ in self.agents.items()]
    def __str__(self):
        return f'{self.clients}\2{self.agents}'

def parseDB(text):
    data=text.split('\2')
    db=DB()
    db.clients=ast.literal_eval(data[0])
    db.agents==ast.literal_eval(data[0])
    return db