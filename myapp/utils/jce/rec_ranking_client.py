import asyncio
import datetime
import re
import time
import traceback
import threading
from .rec_ranking import *
import pysnooper

class REC_RANKING_Client(object):
    SERVANT_NAME = "kubeflow.rpcclients.taf.RecRankingSvrProxy"

    def __init__(self,SERVER_L5_ID):
        self.SERVER_L5_ID=SERVER_L5_ID

    @pysnooper.snoop()
    def get_instance(self, namespace: str, server_name: str):
        import asyncio
        from polaris.api.consumer import create_consumer_by_config
        from polaris.pkg.model.service import GetOneInstanceRequest, ServiceCallResult, RetStatus, GetInstancesRequest
        from polaris.pkg.config.api import Configuration

        config = Configuration()
        config.set_default()
        config.verify()
        # config.consumer_config.get_load_balancer().type = "wr"
        consumer = create_consumer_by_config(config)

        if isinstance(threading.current_thread(), threading._MainThread):
            loop = asyncio.get_event_loop()
        else:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            loop = asyncio.get_event_loop()

        request = GetInstancesRequest(namespace=namespace, service=server_name, timeout=10000)
        ret = loop.run_until_complete(consumer.async_get_instances(request))
        instance = ret.dest_instances
        host = []
        for ins in instance.instances:
            host.append("%s:%s" % (ins.get_host(), ins.get_port()))
        return host

    def _get_rpc_client(self):
        hosts_ports = self.get_instance(namespace='Production',server_name=self.SERVER_L5_ID)
        proxys=[]
        for hosts_port in hosts_ports:
            host,port=hosts_port.split(':')[0],hosts_port.split(':')[1]
            proxy = RecRankingSvrProxy()
            conn_info = "{}@tcp -h {} -p {}".format(self.SERVANT_NAME, host, port)
            print("model server rpc client conn_info='{}'".format(conn_info))
            proxy.locator(conn_info)
            proxys.append(proxy)

        return proxys

    @pysnooper.snoop()
    def query_deploy_status(self, model_name,thr_exp=True):
        clients = self._get_rpc_client()
        req = ModelDetailReq()
        req.modelName = model_name
        result={}
        for client in clients:
            try:
                ret, resp = client.GetModelDetail(req)
                if ret != 0:
                    print("query embedding check failed, req={}, ret={}, resp={}".format(req.toJSON(), ret, resp.toJSON()))
                    raise Exception("query embedding check error: [{}, {}]".format(ret, resp.toJSON()))
                result[client.ip+":"+str(client.port)]=resp.toJSON()
            except Exception as e:
                print("query embedding check error: {}\nreq={}\n{}".format(e, req.toJSON(), traceback.format_exc()))
                if thr_exp:
                    raise e
                result[client.ip+":"+str(client.port)]=None

        return result


if __name__=="__main__":
    rec_ranking_client = REC_RANKING_Client('1961537:212729856')
    result = rec_ranking_client.query_deploy_status(model_name='test')
    message = ''
    for ip in result:
        message += ip + " " + result[ip]
