def get_info():
    return {
        'name':'Sumador',
        'description':'Este agente sirve para sumar',
        'actions':['sum','sum_list','sum_range'],
        'action description':{
            'sum':'Return the sum of the two entries',
            'sum_list':'Return the sum of a collection',
            'sum_range':'Return a list of a range'
        }
    }

class Sumador:
    def __init__(self):
        return
    
    def sum(self,call_agent, args):
        a, b= args
        return str(int(a)+int(b))
    
    def sum_list(self,call_agent, args):
        return sum(args)
    
    def sum_range(self,call_agent, args):
        if len(args)==3:
            a,b,c=args
        if len(args)==2:
            a,b=args
            c=1
        if len(args)==1:
            a=0
            b=args[0]
            c=1
        else:
            return 0
        return sum(range(a,b,c))