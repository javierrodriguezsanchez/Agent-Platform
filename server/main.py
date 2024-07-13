from server import server

if __name__== '__main__':
    MCAST_GRP = '224.1.1.1'
    MCAST_PORT = 5007
    PORT = 5008
    AGENTS_PORT=5009
    s=server(MCAST_GRP, MCAST_PORT, PORT,AGENTS_PORT)
    s.run()