from client_connection import client
from client_interface import client_interface

if __name__=='__main__':
    MCAST_GRP = '224.1.1.1'
    MCAST_PORT = 5010
    PORT=5011
    AGENT_PORT=5012
    client_instance=client(MCAST_GRP, MCAST_PORT, PORT,AGENT_PORT)
    interface=client_interface(client_instance)
    interface.run_interface()