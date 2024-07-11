from server import server

if __name__== '__main__':
    MCAST_GRP = '224.1.1.1'
    MCAST_PORT = 5007
    s=server(MCAST_GRP, MCAST_PORT)
    s.run()