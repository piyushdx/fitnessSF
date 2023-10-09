
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from config import config, environment, ip_config
import re
from fitnesssf1 import FitnessSF
import os
app = Flask(__name__)
CORS(app, support_credentials=True)
import os

fitnessf = FitnessSF()

@app.route('/FitnessSF_clear_cache')
@cross_origin(supports_credentials=True)
def FitnessSF_clear_cache():
    return fitnessf.clear_cache()

@app.route('/FitnessSF_get_response', methods=['POST'])
@cross_origin(supports_credentials=True)
def FitnessSF_get_response():
    return fitnessf.get_response(request.get_json())

if __name__ == '__main__':
    IP = ip_config[environment]
    response_port = config['BotApplication']['Backend']  # response API
    app.run(host='0.0.0.0', port=response_port)

