from agent import agent

def get_info():
    return {
        'name':'Multiplicador',
        'description':'Este agente sirve para multiplicar',
        'actions':['multiplicate','multiplicate_list'],
        'action description':{
            'multiplicate':'Return the multiplication of the two entries',
            'multiplicate_list':'Return the multiplication of a collection'
        }
    }

class Multiplicador(agent):
    def __init__(self):
        return
    
    def multiplicate(self,args):
        a, b= args
        return str(int(a)*int(b))
    
    def multiplicate_list(self,args):
        result=1
        for x in args:
            result*=x
        return result