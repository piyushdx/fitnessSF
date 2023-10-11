from flask import Flask, render_template
import os
import threading
import re
from config import config, environment, ip_config
from flask_csp import csp
from flask_cors import CORS, cross_origin

# ===================================================================================================
IP = ip_config[environment]
response_port = config['BotApplication']['Backend']  # response API

with open("ChatBotUI/static/js/script_base.js", "r", encoding='utf-8') as f:
    js_code= f.read()

js_code = re.sub('"http://127.0.0.1:1563/"', f'"http://{IP}:{response_port}/"', js_code)
# print("js_code*********")
# print(js_code)
with open("ChatBotUI/static/js/script.js", "w") as f:
    f.write(js_code)
    f.close()
# ===================================================================================================


TEMPLATE_DIR = os.path.abspath('ChatBotUI/templates')
STATIC_DIR = os.path.abspath('ChatBotUI/static')

# app = Flask(__name__) # to make the app run without any
app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
CORS(app, resources={r"/fitnesssf": {"origins": "http://localhost:3000"}})
# cors = CORS(app, resources={r"/*": {"origins": "*"}})
# csp = {
#     "default-src": "'self'",
#     "script-src": ["'self'", "/static/"],
#     "style-src": ["'self'", "/static/"],
#     # Add more directives as needed
# }
# talisman = Talisman(app, content_security_policy=csp)
app.config['CSP'] = {
    'default-src': "'self'",
    'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", "/static/"],
    'style-src': ["'self'", "'unsafe-inline'", "/static/"],
    'font-src': ["'self'", 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css', '/static/'],
}


# csp(app)

@app.route('/')
@cross_origin(supports_credentials=True)
def index():
    return "check /fitnesssf"

@app.route('/fitnesssf')
@cross_origin(supports_credentials=True)
def UltraBot():
    return render_template('fitnesssf.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config['BotApplication']['Frontend'])

