def get_info():
    return {
        'name':'Multiplicador',
        'description':'Este agente sirve para multiplicar',
        'actions':['multiplicate','multiplicate_list',
                   #'use_sum_multiplication'
                ],
        'action description':{
            'multiplicate':'Return the multiplication of the two entries',
            'multiplicate_list':'Return the multiplication of a collection'
            #,'use_sum_multiplication': "Usa la suma para multiplicar"
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
'''
    def use_sum_multiplication(self, search_agents, call_agent, args):
        a, b= args
        a=int(a)
        b=int(b)
        count=0
        for i in range(b):
            call=call_agent('Javier_Sumador','sum',(a,count))
            call_results=call.split('\1')
            if call_results[0]=='ERROR':
                return None
            count=int(call_results[1])
        return str(count)
'''