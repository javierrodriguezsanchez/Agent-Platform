class database:
    def __init__(self):
        self.categories=dict()
        self.users=dict()
        self.agents=dict()

    def edit_database(self,messege):
        instructions=messege.split('\1')
        
        if instructions[0]=='GET_AGENTS':
            if instructions[1] in self.categories.keys():
                return str(self.categories[instructions[1]])
            return str(set())
        
        if instructions[0]=='GET_INFO_FOR_AGENT':
            if instructions[1] not in self.agents.keys():
                return 'DISCONNECTED'
            if not self.agents[instructions[1]]['connected']:
                return 'DISCONNECTED'
            return self.agents[instructions[1]]['info']
        
        if instructions[0]=='INSERT_CLIENT':
            exist=(instructions[1] in self.users)
            if not exist:
                self.users[instructions[1]]=instructions[2]
                return str(True)
            return str(False)
        
        if instructions[0]=='NEW_AGENT_TO_ACTION':
            if instructions[1] not in self.categories.keys():
                self.categories[instructions[1]]=[instructions[2]]
            elif instructions[2] not in self.categories[instructions[1]]:
                self.categories[instructions[1]].append(instructions[2])
            return ''
        
        if instructions[0]=='ADD_AGENT' or instructions[0]=='UPDATE_AGENT':
            self.agents[instructions[1]]={
                'info':instructions[1],
                'connected':True,
                'ip':instructions[2]
            }
            return ''

        if instructions[0]=='REMOVE_AGENT_TO_ACTION':
            if instructions[1] not in self.categories.keys():
                return ''
            if instructions[2] in self.categories[instructions[1]]:
                self.categories[instructions[1]].remove(instructions[2])
            return ''
        
        if instructions[0]=='REMOVE_AGENT':
            if instructions[1] in self.agents.keys():
                self.agents.pop(instructions[1])
            return ''


        if instructions[0]=='GET_IP_AGENT':
            if instructions[1] not in self.agents.keys():
                return str(False)
            if not self.agents[instructions[1]]['connected']:
                return 'DISCONNECTED'
            return self.agents[instructions[1]]['ip']
            
        
        if instructions[0]=='AGENT_DISCONNECTED':
            if instructions[1] in self.agents.keys():
                self.agents[instructions[1]]['connected']=False
            return ''