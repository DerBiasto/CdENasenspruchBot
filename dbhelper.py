import sqlite3
import datetime

class Nasenspruch:
    def __init__(self, text, time, active, name=None):
        self.text = text
        #~ try:
            #~ self.time = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
        #~ except:
            #~ self.time = None
        self.time = time
        self.active = active
        self.name = name

class DBHelper:
    def __init__(self, dbname="nasenspruch.sqlite"):
        self.dbname = dbname
        self.c = sqlite3.connect(dbname)
        
    def setup(self):
        q = "CREATE TABLE IF NOT EXISTS nasenspruch(userid text, time text, text text)"
        self.c.execute(q)
        #q = "ALTER TABLE nasenspruch ADD COLUMN active integer DEFAULT 0"
        #self.c.execute(q)
        self.c.commit()
        
    def addSpruch(self, userid, text):
        q = "INSERT INTO nasenspruch (userid, time, text) VALUES (?, ?, ?)"
        args = (userid, datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), text)
        self.c.execute(q, args)
        self.c.commit()
        
    def deleteSprueche(self, userid):
        q = "DELETE FROM nasenspruch WHERE userid = ?"
        args = (userid, )
        self.c.execute(q, args)
        self.c.commit()
        
    def deleteSpruch(self, userid, time):
        q = "DELETE FROM nasenspruch WHERE userid = ? and time = ?"
        args = (userid, time)
        self.c.execute(q, args)
        self.c.commit()
        
    def getSprueche(self, userid=None):
        if userid:
            q = "SELECT text, time, active FROM nasenspruch WHERE userid = ?"
            args = (userid, )
            result = []
            for row in self.c.execute(q, args):
                result.append(Nasenspruch(row[0], row[1], row[2]))
            return result
        else:
            q = "SELECT text, time, active FROM nasenspruch"
            result = []
            for row in self.c.execute(q):
                result.append(Nasenspruch(row[0], row[1], row[2]))
            return result
            
    def setActiveSpruch(self, userid, time=None):
        if time: 
            q = "UPDATE nasenspruch SET active = 0 WHERE userid = ? and time != ?"
            args = (userid, time)
            self.c.execute(q, args)   
            q = "UPDATE nasenspruch SET active = 1 WHERE userid = ? and time = ?"
            args = (userid, time)
            self.c.execute(q, args)
        else:
            q = "UPDATE nasenspruch SET active = 0 WHERE userid = ?"
            args = (userid, )
            self.c.execute(q, args)
        self.c.commit()
        
    def getActiveSpruch(self, userid):
        q = "SELECT text, time, active FROM nasenspruch WHERE userid = ? and active = 1"
        args = (userid, )
        result = []
        for row in self.c.execute(q, args):
            result.append(Nasenspruch(row[0], row[1], row[2]))
        return result
        
        
    
        
