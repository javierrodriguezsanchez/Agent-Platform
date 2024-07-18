import ast
import DB_utils

class DB:
    def __init__(self):
        self.clients=dict()
        self.agents=dict()
        self.logs=dict()
        self.time=0
    def edit_database(self,instruction):
        instruction=instruction.split('\1')
        answer=''
        if instruction[0]=='INSERT_CLIENT':
            answer=self.add_client(instruction[1],instruction[2],instruction[3])
        if instruction[0]=='INSERT_AGENT':
            self.add_agent(instruction[1],instruction[2],instruction[3])
        if instruction[0]=='UPDATE_AGENT':
            self.update_agent(instruction[1],instruction[2])
        if instruction[0]=='CHECK_PASSWORD':
            answer = self.check_password(instruction[1],instruction[2])
        if instruction[0]=='GET_IP_AGENT':
            answer = self.get_ip_agent(instruction[1])
        if instruction[0]=='GET_AGENTS':
            answer = self.get_agents(instruction[1])
        if instruction[0]=='REMOVE_AGENT':
            self.remove_agent(instruction[1])
        if instruction[0]=='GET_LOG':
            answer=self.logs[int(instruction[1])]
        if instruction[0]=='TIME':
            answer=self.time
        if instruction[0]=='FORGET':
            answer=self.forget(hash(instruction[1]),hash(instruction[2]))
        return str(answer)
    def add_client(self,name,password,ip):
        if name in self.clients.keys():
            return False
        self.time+=1
        self.clients[name]=(password,ip)
        self.logs[self.time]=f'INSERT_CLIENT\1{name}\1{password}\1{ip}'
        return True
    def add_agent(self,name,dic,ip):
        self.time+=1
        self.agents[name]=(ast.literal_eval(dic),ip,True)
        self.logs[self.time]='INSERT_AGENT}\1{name}\1{dic}\1{ip}'
    def update_agent(self,name,dic):
        self.time+=1
        info=ast.literal_eval(dic)
        if info[name] not in self.agents[name].keys():
            self.agents[name]=(info,self.agents[name][1],True)
            self.logs[self.time]='UPDATE',name,info
    def check_password(self, name, password):
        return self.clients[name][0]==password
    def get_ip_agent(self,name):
        return self.agents[name][1]
    def get_agents(self,query):
        return [x[0] for y,x in self.agents.items() if query in y]
    def remove_agent(self,name):
        self.time+=1
        if name in self.agents.keys():
            self.agents.pop(name)
            self.logs[self.time]=f"REMOVE_AGENT\1{name}"
    def __str__(self):
        return f'{self.clients}\2{self.agents}\2{self.time}'
    def forget(self,id,id_2):
        self.time+=1
        if id_2>id:
            self.clients={x:y for x,y in self.clients.items() if hash(x)<=id or hash(x)>id_2}
            self.agents={x:y for x,y in self.agents.items() if hash(x)<=id or hash(x)>id_2}
        else:
            self.clients={x:y for x,y in self.clients.items() if id_2<hash(x) and hash(x)<=id}
            self.agents={x:y for x,y in self.agents.items() if id_2<hash(x) and hash(x)<=id}
        self.logs[self.time]=f'FORGET\1{id}\1{id_2}'
    def split(self,id,id_2):
        a=DB()
        b=DB()
        left=min(id,id_2)
        right=max(id,id_2)
        a.clients={x:y for x,y in self.clients.items() if left<hash(x) and hash(x)<=right}
        a.agents={x:y for x,y in self.agents.items() if left<hash(x) and hash(x)<=right}
        b.clients={x:y for x,y in self.clients.items() if hash(x)<=left or hash(x)>right}
        b.agents={x:y for x,y in self.agents.items() if hash(x)<=left or hash(x)>right}

        a.time=self.time
        b.time=self.time
        if id>id_2:
            return (a,b)
        return (b,a)
    
    def join(self,db,transform):
        if transform:
            db=parseDB(db)
        self.time+=1
        self.agents={**self.agents,**db.agents}
        self.clients={**self.clients,**db.clients}
        self.logs[self.time]=f'JOIN\1{db}'
    
    def get_logs(self,time):
        return [y for x,y in self.agents.items() if int(x)>time]

def parseDB(text):
    data=text.split('\2')
    db=DB()
    db.clients=ast.literal_eval(data[0])
    db.agents=ast.literal_eval(data[1])
    db.time=ast.literal_eval(data[2])
    return db