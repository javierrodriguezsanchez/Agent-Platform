from server import server

if __name__== '__main__':
    info={
        'MULTICAST GROUP' : '224.1.1.1' ,
        'MULTICAST PORT' : 5010 ,
        'PORT' : 5011 ,
        'AGENTS PORT' : 5012 ,
        'DATABASE IP':['172.17.0.2'] ,
        'DATABASE GROUP': '224.1.1.2' ,
        'DATABASE PORT' : 5008 ,
        'DATABASE MULTICAST PORT' : 5009,
        'CACHE LIMIT': 1000
    }
    s=server(info)    
    s.run()