
"""Utility functions used across Myapp"""
import sys,os
import numpy as np
from bs4 import BeautifulSoup
import requests,base64,hashlib
from collections import namedtuple
import datetime
from email.utils import make_msgid, parseaddr
import logging
import time,json
from urllib.error import URLError
import urllib.request
import pysnooper
import  re
import croniter
from dateutil.tz import tzlocal
import shutil
import os,sys,io,json,datetime,time
import subprocess
from datetime import datetime, timedelta
import os
import sys
import time
import datetime
from myapp.utils.py.py_k8s import K8s
from myapp.utils.celery import session_scope
from myapp.project import push_message,push_admin
from myapp.tasks.celery_app import celery_app
# Myapp framework imports
from myapp import app, db, security_manager

from myapp.models.model_train_model import Training_Model

@celery_app.task(name="task.list_train_model", bind=True)
def list_train_model(task):
    # 获取
    with session_scope(nullpool=True) as dbsession:
        try:

            train_models = dbsession.query(Training_Model).filter(Training_Model.status == 'online').order_by(Training_Model.id.desc()).all()  # 获取model记录

            train_model_message={}
            for train_model in train_models:
                if train_model.created_by.username not in train_model_message:
                    train_model_message[train_model.created_by.username]=[]
                train_model_message[train_model.created_by.username].append(train_model)

            for username in train_model_message:

                message = '\n用户%s在线模型:\n'%username
                model_num = len(train_model_message[username])
                for train_model in train_model_message[username]:
                    message+=train_model.name+":%s\n"%train_model.created_on.strftime("%Y-%m-%d")
                message+="\n请及时清理不再使用的模型服务"
                if model_num>3:
                    push_admin(message)
                push_message([username],message)
        except Exception as e:
            print(e)




