# app.py
from flask import Flask
import os, socket

app = Flask(__name__)

@app.route('/')
def home():
    hostname = socket.gethostname()
    db_user  = os.environ.get('DB_USER', 'not-set')
    env      = os.environ.get('APP_ENV', 'unknown')
    return f'''
    <html>
    <head><title>Project 4</title></head>
    <body style="font-family:Arial;padding:40px;background:#f0f4f8">
      <h1 style="color:#1E3A5F">Project 4 — ECS Fargate</h1>
      <p><b>Container hostname:</b> {hostname}</p>
      <p><b>Environment: staging</b></p>
      <p><b>DB User (from Secrets Manager):</b> {db_user}</p>
      <p style="color:green"><b>Status:</b> Running on Fargate</p>
    </body></html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)