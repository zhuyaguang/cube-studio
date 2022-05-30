
import sys
import os

dir_common = os.path.split(os.path.realpath(__file__))[0] + '/../'
sys.path.append(dir_common)   # 将根目录添加到系统目录,才能正常引用common文件夹

import traceback
import argparse
from aiohttp import web
import aiohttp

import asyncio
import base64
import logging
import time,datetime
import json
import requests
from aiohttp.web import middleware



routes = web.RouteTableDef()




@routes.get('/')
async def hello(request):
    return web.Response(text="Hello, world")




if __name__ == '__main__':

    app = web.Application(client_max_size=int(10)*1024**2,middlewares=[])    # 创建app，设置最大接收图片大小为2M
    app.add_routes(routes)     # 添加路由映射
    app.router.add_static(prefix='/test', path='web', name='index')  # prefix网址前缀，path本地相对目录，name。这里的目录，是相对于k8s部署时的入口位置来说的

    web.run_app(app,host='0.0.0.0',port=8080)   # 启动app
    logging.info('server close：%s'% datetime.datetime.now())



