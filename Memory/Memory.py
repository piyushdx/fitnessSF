
import os
import sqlite3
from flask import Flask, g, request, jsonify


class Memory:
    def __init__(self, app) -> None:
        pass
    def get_db(self):
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = sqlite3.connect('users.db')
        return db 

    def store_to_database(self,email, bot_name, chat):
        # db = sqlite3.connect('users_chat.db')
        print('get request to store to database',email,bot_name,chat)
        db = self.get_db()
        try:
            c = db.cursor()
            c.execute("INSERT INTO users_chat (email, bot_name, chat) VALUES (?,?,?)", 
                    (email, bot_name, chat))
            db.commit()
            # db.close()
            return jsonify({'result': 'Data Successfully added into database.'})
        except Exception as e:
            print(e)
            db.rollback() # rollback on failure
            db.commit()
            # db.close()
            return jsonify({'error': 'Make sure to provide all details'})
        
    def store_to_chatdb(self,email, chatbot_name):
    
        print('get request to store to chatbot database',email,chatbot_name)
        db = self.get_db()
        c = db.cursor()
        c.execute("SELECT * FROM chatbot_usage WHERE email=? AND chatbot_name=?", (email, chatbot_name))
        row = c.fetchone()
      
        try:                
            if row:
                # If the entry exists, increment the usage_count and update the row
                usage_count = row[2] + 1
                c.execute("UPDATE chatbot_usage SET usage_count=? WHERE email=? AND chatbot_name=?", (usage_count, email, chatbot_name))
          
                
            else:
                # If the entry does not exist, insert a new row with usage_count as 1
                usage_count = 1
                c.execute("INSERT INTO chatbot_usage (email, chatbot_name, usage_count) VALUES (?, ?, ?)", (email, chatbot_name,usage_count))
            db.commit()
            db.close()
            return jsonify({'result': 'Data Successfully added into database.'})
        except Exception as e:
            print(e)
            db.rollback() # rollback on failure
            db.commit()
            db.close()
            return jsonify({'error': 'Make sure to provide all details'})
        
    def get_all_chats(self):
        db = self.get_db()
        c = db.cursor()
        c.execute('SELECT * FROM ')
        chats = c.fetchall()
        return jsonify({'users': chats})

    def get_chats_for_user(self,username):
        db = self.get_db()
        c = db.cursor()
        c.execute('SELECT * FROM users_chat WHERE userid=? ORDER BY time_stamp', (username,))
        chats = c.fetchall()

        return chats
