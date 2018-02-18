import sqlite3
import datetime

class Nasenspruch:
    def __init__(self, text, time, active, id):
        self.text = text
        self.time = time
        self.active = active
        self.id = id

class DBHelper:
    def __init__(self, dbname="nasensprueche.sqlite"):
        self.dbname = dbname
        self.c = sqlite3.connect(dbname)
        
    def setup(self):
        q = "CREATE TABLE IF NOT EXISTS nasenspruch(user_id text, time text, text text, active integer DEFAULT 0, id INTEGER PRIMARY KEY ASC)"
        self.c.execute(q)
        self.c.commit()
        
    def add_spruch(self, user_id, text):
        q = "INSERT INTO nasenspruch (user_id, time, text) VALUES (?, ?, ?)"
        args = (user_id, datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'), text)
        self.c.execute(q, args)
        self.c.commit()
        
    def delete_sprueche(self, user_id):
        q = "DELETE FROM nasenspruch WHERE user_id = ?"
        args = (user_id, )
        self.c.execute(q, args)
        self.c.commit()
        
    def delete_spruch(self, user_id, id):
        q = "DELETE FROM nasenspruch WHERE user_id = ? and id = ?"
        args = (user_id, id)
        self.c.execute(q, args)
        self.c.commit()
        
    def get_sprueche(self, user_id):
        q = "SELECT text, time, active, id FROM nasenspruch WHERE user_id = ?"
        args = (user_id, )
        result = []
        for row in self.c.execute(q, args):
            result.append(Nasenspruch(row[0], row[1], row[2], row[3]))
        return result
            
    def set_active_spruch(self, user_id, id=None):
        q = "UPDATE nasenspruch SET active = 0 WHERE user_id = ?"
        args = (user_id, )
        self.c.execute(q, args)   
        if id:
            q = "UPDATE nasenspruch SET active = 1 WHERE user_id = ? and id = ?"
            args = (user_id, id)
            self.c.execute(q, args)
        self.c.commit()
        
    def get_active_spruch(self, user_id):
        q = "SELECT text, time, active, id FROM nasenspruch WHERE user_id = ? and active = 1"
        args = (user_id, )
        result = self.c.execute(q, args).fetchone()
        if result == None:
            result = []
            q = "SELECT text, time, active, id FROM nasenspruch WHERE user_id = ?"
            args = (user_id, )
            for row in self.c.execute(q, args):
                result.append(Nasenspruch(row[0], row[1], row[2], row[3]))
            
            result.sort(key=lambda x: (x.time), reverse=True)
            if result:
                return result[0]
            else:
                return None
        return Nasenspruch(result[0], result[1], result[2], result[3])
        
