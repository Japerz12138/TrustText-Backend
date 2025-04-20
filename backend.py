#!/bin/python3
from flask import Flask

app = Flask(__name__)

@app.route("/")
def trustText():
    return "<p>Welcome to Trust Text API</p> " \
    "<a>Hello from Japerz</a>"