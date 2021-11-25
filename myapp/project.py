import pysnooper
import requests
from flask_login import current_user, LoginManager
import logging
import json
import jwt
from sqlalchemy.ext.declarative import declared_attr
from flask_babel import lazy_gettext
import time
import hashlib
from typing import List
import requests

from flask_login import login_user, logout_user,login_manager
from flask_appbuilder.security.views import AuthDBView, AuthRemoteUserView
from flask_appbuilder.security.views import expose
import xml.etree.ElementTree as ET
from functools import update_wrapper
from flask import redirect, g, flash, request, session, abort
import pysnooper
import json


# 向admin发送告警
# @pysnooper.snoop()
def push_admin(message):
    try:
        # data = {
        #     "receivers": conf.get('PIPELINE_TASK_BCC_ADDRESS').split(','),
        #     "提示": message
        # }

        data = {
            # "receivers": conf.get('PIPELINE_TASK_BCC_ADDRESS').split(','),
            "msgtype": "rich_text",
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": message
                    }
                }
            ]
        }

        url = "http://api.di.music.woa.com/di/api-center/push?key=kubeflow-admin"
        res = requests.post(url,json=data)
        print(res.content)
    except Exception as e:
        print(e)

# 消息推送
def push_message(receivers,message,link=None):
    try:
        data = {
            "receivers": receivers,
            "msgtype":"rich_text",
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": message
                    }
                }
            ]
        }
        if link:
            for key in link:
                data['rich_text'].append(
                    {
                        "type": "link",
                        "link": {
                            "type": "view",
                            "text": key+"\t",
                            "key": link[key],
                            "browser": 0
                        }
                    }
                )

        url = "http://api.di.music.woa.com/di/api-center/push?key=kubeflow"
        res = requests.post(url,json=data)
        result = res.json()

        if result.get('errcode',-1) == 0:
            print('sent wechat success')
            return
        message = result.get('message','未知原因')
        raise Exception('sent message to rtx fail:%s,message is %s'%(result,message))

    except Exception as e:
        print(e)
        raise Exception('sent message to rtx fail:%s' % (str(e),))

import os


# 自定义远程用户视图
# @pysnooper.snoop()
class MyCustomRemoteUserView(AuthRemoteUserView):

    TMEOA_APPKEY = 'd885366a199acc24402fc006b9b1cfbd'
    TMEOA_APPSECRET = '71223af06081c363d470e268d7e347d1'
    TMEOA_AUTH_URL = 'http://passport.tmeoa.com/authorize?appkey=%s&redirect_uri=%s'
    # TMEOA_LOGOUT_URL = 'http://passport.tmeoa.com/signout?appkey=%s&redirect_uri=%s'
    TMEOA_ENCODE_CODE_URL = 'http://passport.tmeoa.com/authorize/accessToken?code=%s&appkey=%s&app_secret=%s'

    # tme oa，获取username和org
    @pysnooper.snoop(watch_explode=())
    def encrypt_code(self, code):
        def get_header():
            tme_appkey = self.TMEOA_APPKEY
            tme_appsecret = self.TMEOA_APPSECRET
            time_now = str(int(time.time()))
            hash = hashlib.sha1()
            hash.update((time_now + tme_appsecret + time_now).encode('utf-8'))
            signature = hash.hexdigest(),
            header = {
                'Content-Type': 'application/json',
                'X-APPKEY': tme_appkey,
                'X-SIGNATURE': signature[0],
                'X-TIMESTAMP': time_now
            }
            return header

        try:
            appkey = self.TMEOA_APPKEY
            appsecret = self.TMEOA_APPSECRET
            encode_code_url = self.TMEOA_ENCODE_CODE_URL
            url = encode_code_url%(code,appkey,appsecret)
            r = requests.get(url,timeout=5,headers=get_header())
            if r.status_code==200:
                # root = ET.fromstring(r.text.encode('utf8'))
                # user = root.find('{http://indigo.oa.com/services/}LoginName')
                # return user.text,'' or None,None
                print(r.json())
                json_result = r.json()
                if json_result['code']==0:
                    baseUserInfo =json_result['data']['baseUserInfo']
                    if baseUserInfo['orgFullName']:
                        return baseUserInfo['englishName'],'公司其他组织/'+baseUserInfo['orgFullName']
                    else:
                        return baseUserInfo['englishName'], ''
            else:
                message = str(r.content,'utf-8')
                print(message)
        except Exception as e:
            print(e)
        return None, ''


    @expose('/login/tmeoa/')
    def login_tmeoa(self):
        login_url = 'http://%s/login'%request.host
        auth_url = self.TMEOA_AUTH_URL
        appkey = self.TMEOA_APPKEY
        g.user = session.get('user', '')
        if 'code' in request.args:
            g.user, org = self.encrypt_code(request.args.get('code'))
            if g.user: g.user=g.user.replace('.','')

        if 'rtx' in request.args:
            if request.args.get('rtx'):
                g.user = request.args.get('rtx')
                if g.user: g.user = g.user.replace('.', '')

        # remember user
        if (g.user) and g.user != '':
            session['user'] = g.user
            user_now = self.appbuilder.sm.auth_user_remote_org_user(g.user)
            if user_now:
                # 配置session，记录时长等，session_id，用户id等
                login_user(user_now)
                return redirect(self.appbuilder.get_url_for_index)
            else:
                return 'user not active, contact admin'
        else:
            return redirect(auth_url % (str(appkey), login_url))


    OA_APPKEY = '3e55b331e0e84092a1366cd5f6fd2843'  # ioa登录时申请的appkey
    OA_AUTH_URL = 'http://passport.oa.com/modules/passport/signin.ashx?appkey=%s&title=&url=%s'
    OA_LOGOUT_URL = 'http://passport.oa.com/modules/passport/signout.ashx?appkey=%s&redirect_uri=%s'

    @expose('/login/oa/')
    def login_oa(self):
        from myapp import conf  # 引入config配置项,放在函数里面是因为在config文件中也引用了该文件，而conf变量是引入该文件后产生的
        login_url = 'http://%s/login'%request.host
        oa_auth_url= self.OA_AUTH_URL
        appkey = self.OA_APPKEY
        g.user = session.get('user', '')
        if 'ticket' in request.args:
            # user check first login
            data = {'encryptedTicket': request.args.get('ticket')}
            r = requests.post("http://login.oa.com/services/passportservice.asmx/DecryptTicket", data=data,timeout=2)
            if r.status_code == 200:
                root = ET.fromstring(r.text.encode('utf8'))
                user = root.find('{http://indigo.oa.com/services/}LoginName')
                g.user = user.text or None    # 不能if user
                if g.user: g.user = g.user.replace('.', '')

            else:
                message = str(r.content, 'utf-8')
                print(message)
                g.user = None


        if 'rtx' in request.args:
            if request.args.get('rtx'):
                g.user = request.args.get('rtx')
                if g.user: g.user = g.user.replace('.', '')

        if 'rtx_user' in request.args:
            if request.args.get('rtx_user'):
                g.user = request.args.get('rtx_user')
                if g.user: g.user = g.user.replace('.', '')

            # 可以放在头部
        if "rtx_user" in request.headers:
            if request.headers.get('rtx_user'):
                g.user = request.headers.get('rtx_user')
                if g.user: g.user = g.user.replace('.', '')


        # remember user
        if g.user and g.user != '':
            session['user'] = g.user
            # 根据用户org，创建同名角色。
            # get user and password
            user_now = self.appbuilder.sm.auth_user_remote_org_user(g.user)
            if user_now:
                # 配置session，记录时长等，session_id，用户id等
                login_user(user_now)
                return redirect(self.appbuilder.get_url_for_index)
            else:
                return 'user not active, contact admin'
        else:
            return redirect(oa_auth_url % (str(appkey),login_url,))



    @expose('/login/')
    def login(self):
        host=request.host
        if 'tmeoa' in host:
            return self.login_tmeoa()
        else:
            return self.login_oa()

    @expose('/logout')
    def logout(self):
        login_url = 'http://%s/login/' % request.host
        logout_url = self.OA_LOGOUT_URL
        appkey = self.OA_APPKEY
        session.pop('user', None)
        g.user = None
        logout_user()
        return redirect(logout_url % (str(appkey), login_url,))


# 账号密码登录方式的登录界面
class Myauthdbview(AuthDBView):
    login_template = "appbuilder/general/security/login_db.html"

