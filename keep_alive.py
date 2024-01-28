from flask import Flask
from threading import Thread

app = Flask('Michiko')

@app.route('/')
def main():
   return "🟢 Michiko API is Operational"

def run():
   app.run(host="0.0.0.0", port=8080)

def keep_alive():
   server = Thread(target=run)
   server.start()