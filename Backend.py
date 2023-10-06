from flask import Flask, render_template, request, jsonify, g
from flask_cors import CORS, cross_origin
from MembeshipBot import MembershipBot
from config import config, environment, ip_config
import re
import sqlite3
import os
from Memory import Memory
from Generative_Agent import init_Generative_Agent

azure_openai_engine = init_Generative_Agent()

app = Flask(__name__)
CORS(app, support_credentials=True)

memory = Memory(app)
membership_bot = MembershipBot("DX-GPT35-16k", memory)

    
@app.route('/Membership_clear_cache', methods=['POST'])
@cross_origin(supports_credentials=True)
def Membership_clear_cache():
    return membership_bot.clear_cache(request.get_json())

@app.route('/Membership_get_response', methods=['POST'])
@cross_origin(supports_credentials=True)
def Membership_get_response():
    return membership_bot.get_response(request.get_json())

@app.route('/health')
def check_health():
    return "Server is Working Fine :)"

if __name__ == '__main__':
    IP = ip_config[environment]
    response_port = config['BotApplication']['Backend']  # response API
    app.run(host='0.0.0.0', port=response_port)
