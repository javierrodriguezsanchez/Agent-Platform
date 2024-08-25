import ast

def get_info():
    return {
        'name':'Multiplicador',
        'description':'Este agente sirve para multiplicar',
        'actions':['multiplicate','multiplicate_list',
                   'use_sum_multiplication'
                ],
        'action description':{
            'multiplicate':'Return the multiplication of the two entries',
            'multiplicate_list':'Return the multiplication of a collection'
            ,'use_sum_multiplication': "Usa la suma para multiplicar"
        }
    }

class Multiplicador:
    def __init__(self):
        return
    
    def multiplicate(self, search_agents, call_agent, args):
        a, b= args
        return str(int(a)*int(b))
    
    def multiplicate_list(self, search_agents, call_agent, args):
        result=1
        for x in args:
            result*=x
        return result
    

    def use_sum_multiplication(self, search_agents, call_agent, args):
        
        a, b= args
        a=int(a)
        b=int(b)
        count=0 #SAVE THE RESULT
        step=0  #ITERATION NUMBER
        
        while True:
            response=search_agents('sum').split('\1')   #SEARCH SUM AGENTS
            
            if response[0]=="ERROR":
                return "No se encontraron agentes sumadores"
    
            agents=ast.literal_eval(response[1])
            for agent in agents:
                if agent['action description']['sum']!='Return the sum of the two entries':
                    continue
                while step!=b:
                    call=call_agent(agent['name'],'sum',(a,count))
                    call_results=call.split('\1')
                    if call_results[0]=='ERROR':
                        break
                    count=int(call_results[1])
                    step+=1
                if step==b:
                    return str(count)