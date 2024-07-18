from DB_connection import DB_connection

if __name__=="__main__":
    MCAST_GROUP='224.1.1.2'
    PORT=5008
    MCAST_PORT=5009
    DB_connection(PORT,MCAST_PORT,MCAST_GROUP)