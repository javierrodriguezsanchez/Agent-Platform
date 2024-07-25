from client_connection import connection
from client_interface import client_interface

if __name__=='__main__':
    info={
        'SERVER GROUP' : '224.1.1.1' ,
        'SERVER MULTICAST PORT' : 5010 ,
        'SERVER PORT' : 5011 ,
        'AGENT PORT' : 5012 ,
        'SERVER IP' : []
    }
    client_connection=connection(info)
    interface=client_interface(client_connection)
    interface.run_interface()