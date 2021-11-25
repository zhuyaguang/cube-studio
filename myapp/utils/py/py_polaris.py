import time,datetime,logging,os,sys

import re

import yaml
from os import path
import json
# from common.config import *
import pysnooper
import base64
import uuid
import requests

# K8s操作类型
class Polaris():

    def __init__(self):
        self.headers={
            "Platform-Id":"kubeflow",
            "Platform-Token":"2f616875096c4c54a8ebd9a84e44de39",
            "Content-Type": "application/json"
        }
        self.host = "http://polaris-api-v2.woa.com:8080"

    def get_service(self,service_name):
        try:
            url = self.host+"/naming/v1/services?name=%s&namespace=%s"%(service_name,'Production')
            res = requests.get(url,headers=self.headers)
            result = res.json()
            # print(result)
            if 'code' in result and result['code'] == 200000:
                return result['services']

        except Exception as e:
            print(e)
        return False


    def register_service(self,usernames,service_name):
        try:
            url =self.host+"/naming/v1/services"
            body=[
                {
                    "name":service_name,
                    "namespace":"Production",
                    "metadata":{
                    },
                    "ports":'',
                    "business":"tme-kubeflow",
                    "department":"腾讯音乐娱乐",
                    "cmdb_mod1":"",
                    "cmdb_mod2":"",
                    "cmdb_mod3":"",
                    "comment":"机器学习平台模型服务",
                    "owners":','.join(set(list(usernames.split(',')))),
                    "platform_id":"kubeflow"
                }
            ]
            res = requests.post(url,json=body, headers=self.headers)
            result = res.json()
            # print(result)
            if 'code' in result and result['code']==200000:
                return result['responses'][0]['service']
        except Exception as e:
            print(e)
        return False



    # @pysnooper.snoop()
    def delete_service(self,service_name):
        try:
            url = self.host+"/naming/v1/services/delete"
            body = [
                {
                    "name": service_name,
                    "namespace": 'Production'
                }
            ]
            res = requests.post(url,json=body,headers=self.headers)
        except Exception as e:
            print(e)
        return False


    def get_instances(self,service_name):
        try:
            url = self.host + "/naming/v1/instances?service=%s&namespace=%s"%(service_name,'Production')
            res = requests.get(url,headers=self.headers)
            result = res.json()
            # print(result)
            if 'code' in result and result['code'] == 200000:
                return result['instances']
        except Exception as e:
            print(e)
        return False

    def register_instances(self,service_name,hosts,port):
        body = []
        for host in hosts:
            body.append(
                {
                    "service": service_name,
                    "namespace": "Production",
                    "host": host,
                    "port": port,
                    "protocol": "http",
                    "version": "v1",
                    "weight": 100,
                    "enable_health_check":False,
                    "health_check": {
                        "type": 1,
                        "heartbeat": {
                            "ttl": 5
                        }
                    },
                    "healthy": True,
                    "isolate": False,
                    "metadata": {
                    }
                }
            )
        try:
            url = self.host + "/naming/v1/instances"
            res = requests.post(url,json=body,headers=self.headers)
            result = res.json()
            # print(result)
            if 'code' in result and result['code'] == 200000:
                return [instance['instance'] for instance in result['responses']]
        except Exception as e:
            print(e)
        return False

    def delete_instances(self,service_name):
        instances = self.get_instances(service_name)
        ids = [instance['id'] for instance in instances]
        try:
            url =self.host+"/naming/v1/instances/delete"
            body=[
                {"id":id} for id in ids
            ]
            res = requests.post(url,json=body, headers=self.headers)
        except Exception as e:
            print(e)
        return False


    def register_alias(self,usernames,service_name):
        try:
            url =self.host+"/naming/v1/service/alias/no-auth"
            body={
                "service":service_name,
                "namespace":"Production",
                "type":1,
                "owners":','.join(set(list(usernames.split(',')))),
                "comment":"tme kubeflow机器学习平台模型服务"
            }
            res = requests.post(url,json=body, headers=self.headers)
            result = res.json()
            # print(result)
            if 'code' in result and result['code']==200000:
                return result['alias']
        except Exception as e:
            print(e)
        return False

    # @pysnooper.snoop()
    def get_alias(self,service_name):
        try:
            url = self.host+"/naming/v1/service/aliases?service=%s&namespace=%s"%(service_name,'Production')
            res = requests.get(url,headers=self.headers)
            result = res.json()
            print(result)
            if 'code' in result and result['code']==200000:
                return result['aliases']
        except Exception as e:
            print(e)
        return False


    # @pysnooper.snoop()
    def delete_alias(self,service_name,alias_token):
        alias = self.get_alias(service_name)
        print(alias)
        try:
            url = self.host+"/naming/v1/services/delete"
            body=[
                {
                    "name":alia['alias'],
                    "namespace":"Production",
                    "token":alias_token.get(alia['alias'],'')
                }
                for alia in alias
            ]
            res = requests.post(url,json=body, headers=self.headers)
        except Exception as e:
            print(e)
        return False


    #
    #
    # def register_circuitbreakers(self,usernames,service_name):
    #     try:
    #         url =self.host+"/naming/v1/circuitbreakers"
    #         body=[
    #             {
    #                 "name":service_name+".kubeflow",
    #                 "namespace":"Production",
    #                 "owners":','.join(set(list(usernames.split(',')))),
    #                 "business": "tme-kubeflow",
    #                 "department": "腾讯音乐娱乐",
    #                 "comment":"tme kubeflow机器学习平台模型服务",
    #                 "inbounds":[]
    #             }
    #         ]
    #         res = requests.post(url,json=body, headers=self.headers)
    #         result = res.json()
    #         print(result)
    #         if 'code' in result and result['code']==200000:
    #             return result['circuitBreaker']
    #     except Exception as e:
    #         print(e)
    #     return False
    #
    # # @pysnooper.snoop()
    # def get_circuitbreakers(self,service_name):
    #     try:
    #         url = self.host+"/naming/v1/service/aliases?service=%s&namespace=%s"%(service_name,'Production')
    #         res = requests.get(url,headers=self.headers)
    #         result = res.json()
    #         print(result)
    #         if 'code' in result and result['code']==200000:
    #             return result['aliases']
    #     except Exception as e:
    #         print(e)
    #     return False
    #
    #
    # # @pysnooper.snoop()
    # def delete_circuitbreakers(self,service_name):
    #     alias = self.get_alias(service_name)
    #     print(alias)
    #     try:
    #         url = self.host+"/naming/v1/services/delete"
    #         body=[
    #             {
    #                 "name":alia['alias'],
    #                 "namespace":"Production",
    #                 "token":alias_token.get(alia['alias'],'')
    #             }
    #             for alia in alias
    #         ]
    #         res = requests.post(url,json=body, headers=self.headers)
    #     except Exception as e:
    #         print(e)
    #     return False
    #
    #
#
#
# if __name__=='__main__':
#     polaris = Polaris()
#     service_name = 'nginx.service'
#     username='pengluan'
#     circuitbreakers = polaris.register_circuitbreakers(username,service_name)
#     print(circuitbreakers)
#
# #     polaris.delete_service(service_name)
# #     service = polaris.register_service('pengluan', 'lstm-year.service')
# #     print(service)
# #     service_token = service['token'] if service else ''
# #
# #     instances = polaris.register_instances(service_name,['10.101.142.24'],30022)
# #     print(instances)
# #
# #     alias = polaris.register_alias(username,service_name)
# #     for alia in alias:
# #         alia_token[alia['alias']]=alia['service_token']
# #     print(service_token)
# # #
