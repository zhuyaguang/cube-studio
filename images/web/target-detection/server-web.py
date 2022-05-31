
import sys
import os

dir_common = os.path.split(os.path.realpath(__file__))[0] + '/../'
sys.path.append(dir_common)   # 将根目录添加到系统目录,才能正常引用common文件夹

import traceback
import argparse
import aiohttp

import asyncio
import base64
import logging
import time,datetime
import json
import requests
from flask import redirect


from flask import Flask

app = Flask(__name__,
            static_url_path='/static',
            static_folder='static',
            template_folder='templates')

@app.route('/api/v1.0/model')
def model():
    return redirect('/static/index.html')


@app.route('/')
def hello():
    return redirect('/static/index.html')

if __name__=='__main__':

    app.run(host='0.0.0.0',debug=True,port='8080')

