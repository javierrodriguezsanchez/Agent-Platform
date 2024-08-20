from DB_utils import *
import ast

class database:
    def __init__(self, id=0):
        self.CATEGORIES=dict()  # category  ->  agents list
        self.USERS=dict()       # name      ->  ip
        self.AGENTS=dict()      # name      ->  (info , ip, connected)
        self.LOGS=dict()        # moment    ->  log

        self.LAMPORT_CLOCK=0
        self.ID_LIST=[id]*4 
        '''
            ID_LIST CONTAINS THE DATABASE FRONTIERS
            ID_LIST[1] - ID_LIST[0]: MAIN PART OF THE DATABASE
            ID_LIST[2] - ID_LIST[1]: COPY OF PREDECCESSOR DATABASE
            ID_LIST[3] - ID_LIST[2]: COPY OF PREDECCESSOR'S PREDECCESSOR DATABASE
        '''


    def time(self):return self.LAMPORT_CLOCK
    def id(self): return str(self.ID_LIST)

    # BASIC OPERATIONS OF THE DATABASE
    # --------------------------------
    def edit_database(self,messege):
        instructions=messege.split('\1')

        if instructions[0]=='GET_AGENTS':
            if instructions[1] in self.CATEGORIES.keys():
                return str(self.CATEGORIES[instructions[1]])
            return str(set())
        
        if instructions[0]=='GET_INFO_FOR_AGENT':
            if instructions[1] not in self.AGENTS.keys():
                return 'DISCONNECTED'
            if not self.AGENTS[instructions[1]]['connected']:
                return 'DISCONNECTED'
            return self.AGENTS[instructions[1]]['info']
        
        if instructions[0]=='GET_IP_AGENT':
            if instructions[1] not in self.AGENTS.keys():
                return str(False)
            if not self.AGENTS[instructions[1]]['connected']:
                return 'DISCONNECTED'
            return self.AGENTS[instructions[1]]['ip']

        if instructions[0]=='INSERT_CLIENT':
            exist=(instructions[1] in self.USERS)
            if not exist:
                self.USERS[instructions[1]]=instructions[2]
                self.LOGS[self.LAMPORT_CLOCK] = messege
                self.LAMPORT_CLOCK+=1
                return str(True)
            return str(False)
        
        if instructions[0]=='NEW_AGENT_TO_ACTION':
            if instructions[1] not in self.CATEGORIES.keys():
                self.CATEGORIES[instructions[1]]=[instructions[2]]
            elif instructions[2] not in self.CATEGORIES[instructions[1]]:
                self.CATEGORIES[instructions[1]].append(instructions[2])
        
        if instructions[0]=='ADD_AGENT' or instructions[0]=='UPDATE_AGENT':
            self.AGENTS[instructions[1]]={
                'info':instructions[1],
                'connected':True,
                'ip':instructions[2]
            }
            
        if instructions[0]=='REMOVE_AGENT_TO_ACTION':
            if instructions[1] not in self.CATEGORIES.keys():
                if instructions[2] in self.CATEGORIES[instructions[1]]:
                    self.CATEGORIES[instructions[1]].remove(instructions[2])            
        
        if instructions[0]=='REMOVE_AGENT':
            if instructions[1] in self.AGENTS.keys():
                self.AGENTS.pop(instructions[1])
            
        if instructions[0]=='AGENT_DISCONNECTED':
            if instructions[1] in self.AGENTS.keys():
                self.AGENTS[instructions[1]]['connected']=False
            
        #ADD LOG
        self.LOGS[self.LAMPORT_CLOCK] = messege
        self.LAMPORT_CLOCK+=1
        
        #DEFAULT RESPONSE
        return ''
        
    # SPECIAL OPERATIONS
    # ------------------
    def migrate_left(self, id):
        '''
            Give data to new anteccessor  
        '''
        db = database()
        db.LAMPORT_CLOCK=self.LAMPORT_CLOCK
        db.CATEGORIES={x:y for x,y in self.CATEGORIES if not is_successor(id, x, self.ID_LIST[0])}
        db.USERS={x:y for x,y in self.USERS if not is_successor(id, x, self.ID_LIST[0])}
        db.AGENTS={x:y for x,y in self.AGENTS if not is_successor(id, x, self.ID_LIST[0])}
        db.ID_LIST=[x for x in self.ID_LIST]
        db.ID_LIST[0]=int(id)
        return db


    def migrate_right(self):
        '''
            Give data to new successor
        '''
        db = database()
        db.LAMPORT_CLOCK=self.LAMPORT_CLOCK
        db.CATEGORIES={x:y for x,y in self.CATEGORIES if is_successor(self.ID_LIST[2], x, self.ID_LIST[0])}
        db.USERS={x:y for x,y in self.USERS if is_successor(self.ID_LIST[2], x, self.ID_LIST[0])}
        db.AGENTS={x:y for x,y in self.AGENTS if is_successor(self.ID_LIST[2], x, self.ID_LIST[0])}
        db.ID_LIST= [x for x in self.ID_LIST]
        return db 


    def upd_id(self, reference_id):
        _id=[self.ID_LIST[0]]+ast.literal_eval(reference_id)[:-1]
        _id=[int(x) for x in _id]
        if self.ID_LIST == _id:
            return False
        self.ID_LIST=_id
        return True
        

    def forget(self):
        if self.ID_LIST[3] in self.ID_LIST[:2]:
            return
        self.CATEGORIES={x:y for x,y in self.CATEGORIES if is_successor(self.ID_LIST[3], x, self.ID_LIST[0])}
        self.USERS={x:y for x,y in self.USERS if is_successor(self.ID_LIST[3], x, self.ID_LIST[0])}
        self.AGENTS={x:y for x,y in self.AGENTS if is_successor(self.ID_LIST[3], x, self.ID_LIST[0])}
        

    def give_logs(self, time):
        return [y for x,y in self.LOGS if x>=time]


    def execute_logs(self, logs):
        logs=ast.literal_eval(logs)
        for log in logs:
            self.edit_database(log)


    def join(self, db):
        '''
            Recieves a database, joins the elements and return the difference
        '''
        for category in db.CATEGORIES.keys():
            self.CATEGORIES[category]=db.CATEGORIES[category]
        for user in db.USERS.keys():
            self.USERS[user]=db.USERS[user]
        for agent in db.AGENTS.keys():
            self.AGENTS[agent]=db.AGENTS[agent]
        if not self.upd_id(str(db.ID_LIST)):
            return False
        return True
    

    def __str__(self):
        return f'{self.ID_LIST}\2{self.USERS}\2{self.AGENTS}\2{self.CATEGORIES}\2{self.LAMPORT_CLOCK}'
    

def parseDB(text):
    data=text.split('\2')
    db=database()
    db.ID_LIST=ast.literal_eval(data[0])
    db.USERS=ast.literal_eval(data[1])
    db.AGENTS=ast.literal_eval(data[2])
    db.CATEGORIES=ast.literal_eval(data[3])
    db.LAMPORT_CLOCK=ast.literal_eval(data[4])
    return db