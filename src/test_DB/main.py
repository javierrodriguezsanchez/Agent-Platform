from DB_connection import DB_connection

if __name__=="__main__":
    info={
        'MULTICAST GROUP' : '224.1.1.2' ,
        'MULTICAST PORT' : 5009 ,
        'PORT' : 5008
    }
    db=DB_connection(info)
    db.run()