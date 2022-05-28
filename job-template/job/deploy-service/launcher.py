
import os,sys
base_dir = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(base_dir)

import argparse
import datetime
import json
import time
import uuid
import os
import pysnooper
import os,sys
import re
import requests
import psutil
import copy
KFJ_CREATOR = os.getenv('KFJ_CREATOR', '')
host = 'http://kubeflow-dashboard.infra/service_modelview/api/'
# @pysnooper.snoop()
def deploy(**kwargs):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': KFJ_CREATOR
    }

    # 查询同名是否存在，创建者是不是指定用户
    filters=[
        {
            "col": "name",
            "opr": "eq",
            "value": kwargs['name']
        }
    ]
    url = host+"?form_data="+json.dumps({
        "filters":filters
    })
    exist_services = requests.get(url)
    print(exist_services)



if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser("deploy service launcher")
    arg_parser.add_argument('--project_name', type=str, help="所属项目组", default='public')
    arg_parser.add_argument('--name', type=str, help="服务名", default='demo')
    arg_parser.add_argument('--label', type=str, help="服务中文名", default='演示服务')
    arg_parser.add_argument('--image', type=str, help="镜像", default='')
    arg_parser.add_argument('--workdir', type=str, help="工作目录", default='')
    arg_parser.add_argument('--command', type=str, help="启动命令", default='')
    arg_parser.add_argument('--env', type=str, help="环境变量", default='')
    arg_parser.add_argument('--resource_memory', type=str, help="内存", default='2G')
    arg_parser.add_argument('--resource_cpu', type=str, help="cpu", default='2')
    arg_parser.add_argument('--resource_gpu', type=str, help="gpu", default='0')
    arg_parser.add_argument('--replicas', type=str, help="副本数", default='1')
    arg_parser.add_argument('--ports', type=str, help="端口号", default='80')
    arg_parser.add_argument('--host', type=str, help="域名", default='0')
    arg_parser.add_argument('--volume_mount', type=str, help="挂载", default='')


    args = arg_parser.parse_args()
    print("{} args: {}".format(__file__, args))

    deploy(**args)


