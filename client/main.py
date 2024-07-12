from client_connection import client
from client_interface import run_interface

if __name__=='__main__':
    MCAST_GRP = '224.1.1.1'
    MCAST_PORT = 5007
    PORT=5008
    client_instance=client(MCAST_GRP, MCAST_PORT, PORT)
    run_interface(client_instance)