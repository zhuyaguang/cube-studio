from flask import render_template,redirect
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask import Blueprint, current_app, jsonify, make_response, request
# 将model添加成视图，并控制在前端的显示
from myapp.models.model_embedding import Embedding
from myapp.models.model_job import Pipeline
from myapp.models.model_team import Project,Project_User
from myapp.utils import core
from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
from flask_appbuilder.actions import action
from myapp import app, appbuilder,db,event_logger
import logging
import re
import uuid
import requests
from myapp.exceptions import MyappException
from flask_appbuilder.security.decorators import has_access
from flask_wtf.file import FileAllowed, FileField, FileRequired
from werkzeug.datastructures import FileStorage
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from myapp import security_manager
import os,sys
from wtforms.validators import DataRequired, Length, NumberRange, Optional,Regexp
from wtforms import BooleanField, IntegerField, SelectField, StringField,FloatField,DateField,DateTimeField,SelectMultipleField,FormField,FieldList
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget,BS3PasswordFieldWidget,DatePickerWidget,DateTimePickerWidget,Select2ManyWidget,Select2Widget
from myapp.forms import MyBS3TextAreaFieldWidget,MySelect2Widget,MyCodeArea,MyLineSeparatedListField,MyJSONField,MyBS3TextFieldWidget,MySelectMultipleField
from myapp.utils.py import py_k8s
import os, zipfile
import shutil
from flask import (
    current_app,
    abort,
    flash,
    g,
    Markup,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    Response,
    url_for,
)
from .base import (
    DeleteMixin,
    api,
    BaseMyappView,
    check_ownership,
    CsvResponse,
    data_payload_response,
    DeleteMixin,
    generate_download_headers,
    get_error_msg,
    get_user_roles,
    handle_api_exception,
    json_error_response,
    json_success,
    MyappFilter,
    MyappModelView,

)
from sqlalchemy import and_, or_, select
from .baseApi import (
    MyappModelRestApi
)


from flask_appbuilder import CompactCRUDMixin, expose
import pysnooper,datetime,time,json
conf = app.config


class Embedding_Filter(MyappFilter):
    # @pysnooper.snoop()
    def apply(self, query, func):
        user_roles = [role.name.lower() for role in list(self.get_user_roles())]
        if "admin" in user_roles:
            return query
        return query.filter(self.model.created_by_fk == g.user.id)



# 定义数据库视图
# class Embedding_ModelView(JsonResModelView,DeleteMixin):
class Embedding_ModelView_Base():

    datamodel = SQLAInterface(Embedding)
    base_permissions = ['can_add', 'can_edit', 'can_delete', 'can_list', 'can_show']  # 默认为这些
    base_order = ('created_on', 'desc')
    order_columns = ['created_on']
    list_columns = ['id','model_name','project_url','pipeline_url','creator','version','is_fallback','status','metrics_str','check_service','prod_deploy']
    add_columns = ['project','pipeline', 'model_name', 'version', 'describe','is_fallback','run_id', 'model_path', 'embedding_file_path', 'metrics','status']
    edit_columns = add_columns
    label_title = 'Embedding'
    base_filters = [["id", Embedding_Filter, lambda: []]]  # 设置权限过滤器
    help_url = conf.get('HELP_URL', {}).get(datamodel.obj.__tablename__, '') if datamodel else ''

    def filter_project():
        query = db.session.query(Project)
        user_roles = [role.name.lower() for role in list(get_user_roles())]
        if "admin" in user_roles:
            return query.filter(Project.type=='embedding').order_by(Project.id.desc())

        # 查询自己拥有的项目
        my_user_id = g.user.get_id() if g.user else 0
        owner_ids_query = db.session.query(Project_User.project_id).filter(Project_User.user_id == my_user_id)

        return query.filter(Project.id.in_(owner_ids_query)).filter(Project.type=='embedding').order_by(Project.id.desc())

    add_form_extra_fields = {
        "project": QuerySelectField(
            _('Embedding服务项目组'),
            description=_('如果没有可选项目组，可联系管理员加入到项目组中'),
            query_factory=filter_project,
            allow_blank=False,
            widget=Select2Widget()
        ),
        "run_id": StringField(
            _(datamodel.obj.lab('run_id')),
            widget=MyBS3TextFieldWidget(),
            description='pipeline 训练的run id',
            default='random_run_id_' + uuid.uuid4().hex[:32]
        ),
    }
    edit_form_extra_fields = add_form_extra_fields




    # 复制模型文件
    @pysnooper.snoop(watch_explode=("group",))
    def deploy(self,embedding):
        try:

            # 查看创建七彩石的分组
            from rainbow_admin import RainbowAdmin
            admin = RainbowAdmin(
                # env='test',
                app_id="60dfd88e-3d06-461a-b5ff-6e87c9c89faf",
                user_id="3a7f2dacdfae40d480e121b2a59a8b37",
                secret_key="2ea307b84a20ac71408eb7d5283aab171dab"
            )
            USER = 'Rainbow_pengluan'
            # 添加ef分组信息，通过七彩石global分组信息来实现
            global_group = admin["global"]
            if 'groups' in global_group:
                ef_monitor_group = global_group['groups']
            else:
                ef_monitor_group=''
            ef_monitor_group = ef_monitor_group.split(',')
            ef_monitor_group = [ef_group.strip() for ef_group in ef_monitor_group if ef_group.strip()] + [embedding.project.name]
            ef_monitor_group = list(set(ef_monitor_group))
            ef_monitor_group = ','.join(ef_monitor_group)


            project_group = admin["%s"%embedding.project.name]
            if not project_group:
                admin.create_group("%s"%embedding.project.name)
                project_group = admin["%s" % embedding.project.name]
                flash('七彩石分组%s创建成功'%embedding.project.name,'success')
                time.sleep(1)


            # 添加配置。先添加空的emb_ver和warn_rtx，然后添加group  然后再给emb_ver和 warn_rtx 赋值
            if project_group:
                print(project_group.configs)
                if 'emb_ver' in project_group:
                    ver = project_group["emb_ver"]   # = embedding.to_json()
                else:
                    ver={}
                if 'warn_rtx' in project_group:
                    warn_rtx = project_group["warn_rtx"]   # = embedding.to_json()
                else:
                    warn_rtx={}

                if not ver:
                    ver={}
                    project_group["emb_ver"] = {}
                if not warn_rtx:
                    warn_rtx = {}
                    project_group['warn_rtx']={}

                if not ver or not warn_rtx:
                    try:
                        project_group.one_click_release(creator=USER, updators=USER, approvers=USER,force_ignore_approval=True)
                        time.sleep(1)
                    except Exception as e:
                        print(e)
                        if '无配置修改' not in str(e):
                            raise e


                global_group['groups'] = ef_monitor_group
                try:
                    global_group.one_click_release(creator=USER, updators=USER, approvers=USER,force_ignore_approval=True)
                except Exception as e:
                    print(e)
                    if '无配置修改' not in str(e):
                        raise e

                time.sleep(1)
                alert_user = [embedding.created_by.username]
                alert_user+=embedding.pipeline.alert_user.split(',') if embedding.pipeline and embedding.pipeline.alert_user else []
                alert_user+=[embedding.pipeline.created_by.username]
                alert_user = list(set(alert_user))

                ver[embedding.model_name] = embedding.version
                warn_rtx[embedding.model_name]= ','.join(alert_user)
                project_group["emb_ver"] = ver
                project_group['warn_rtx']=warn_rtx
                try:
                    project_group.one_click_release(creator=USER, updators=USER, approvers=USER,force_ignore_approval=True)
                except Exception as e:
                    print(e)
                    if '无配置修改' not in str(e):
                        raise e

                url = 'http://rainbow.oa.com/console/60dfd88e-3d06-461a-b5ff-6e87c9c89faf/Default/list?group_id=%s&group_name=%s'%(project_group.group_id,project_group.group_name)
                flash('七彩石分组%s，配置%s下发成功，七彩石地址：%s' % (embedding.project.name,'emb_ver',url), 'success')



        except Exception as e:
            flash('添加七彩石配置失败，请重新操作：%s'%str(e),'warning')


    # 调用jce服务
    @pysnooper.snoop(watch_explode=('data',))
    def post_ef(self,method,param):
        header={
            "Content-Type": "application/json"
        }
        data={
            "comm":"",
            "music.ai.EFIndexSvr.%s"%method:{
                "module":"music.ai.EFIndexSvr",
                "method":method,
                "param":param
            }
        }
        res = requests.post('http://ut.y.qq.com/cgi-bin/musicu.fcg',headers=header,json=data)
        return res


    # 清理部署文件
    @pysnooper.snoop()
    def delete_deploy_version(self,embedding):
        model_deploy_host_dir, model_deploy_container_dir = conf.get('GLOBAL_PVC_MOUNT')['kubeflow-model-deploy'][0], conf.get('GLOBAL_PVC_MOUNT')['kubeflow-model-deploy'][1]

        # model server 删除
        try:
            des_dir = model_deploy_host_dir + "product/"
            if embedding.project:
                des_dir += embedding.project.name

            # des_dir = model_deploy_host_dir + "test/"

            # 删除生产环境目录
            des_path = os.path.join(des_dir, embedding.model_name,embedding.version,'online')
            if os.path.exists(des_path):
                file = open(des_path+"/model.delete",mode='w')
                file.write('')
                file.close()
            flash("model server %s 删除成功"%(embedding.project.name+embedding.model_name+embedding.version,),'success')

        except Exception as e:
            flash("model server error:"+str(e),'warning')

        # ef server 删除
        try:
            data={
                "project":embedding.project.name,
                "model_name":embedding.model_name,
                "version":embedding.version
            }
            res = self.post_ef('removeModelEmb',data)
            if res.status_code==200:
                flash("ef server: %s:%s:%s 删除成功: %s"%(embedding.project.name,embedding.model_name,embedding.version,json.dumps(res.json().get("music.ai.EFIndexSvr.removeModelEmb",{}))),'success')
            else:
                raise Exception(str(res.content,encoding='utf-8'))

        except Exception as e:
            flash("ef server error:"+str(e),'warning')

        # push_admin('\nuser: %s\nembedding: %s模型服务，%s版本下线\nstatus: 下线前状态%s' % (embedding.created_by.username, embedding.model_name,embedding.version,self.old_item['status']))
        return redirect('/embedding_modelview/list/')

    @pysnooper.snoop()
    def pre_json_load(self,req_json):
        try:
            # 将传过来project名称转化为project id
            if 'project_id' in req_json:
                req_json['project'] = int(req_json['project_id'])
            elif 'project' in req_json:
                if type(req_json['project'])==str and not req_json['project'].isdigit():
                    project = db.session.query(Project).filter(Project.name==req_json['project']).filter(Project.type=='embedding').first()
                    if project:
                        req_json['project']=project.id
                else:
                    req_json['project'] = int(req_json['project'])
            # 将传过来的pipeline=$pipeline_id的情况
            if 'pipeline_id' in req_json:
                req_json['pipeline'] = int(req_json['pipeline_id'])
            elif 'pipeline' in req_json:
                if type(req_json['pipeline'])==str and not req_json['pipeline'].isdigit():
                    project = db.session.query(Pipeline).filter(Pipeline.name==req_json['pipeline']).first()
                    if project:
                        req_json['pipeline']=project.id
                else:
                    req_json['pipeline'] = int(req_json['pipeline'])

            if 'filters' in req_json and type(req_json['filters']==list):
                for col in req_json['filters']:
                    if col['col']=='project' and type(col['value'])==str and not col['value'].isdigit():
                        project = db.session.query(Project).filter(Project.name == col['value']).filter(Project.type == 'embedding').first()
                        if project:
                            col['value'] = project.id
                    if col['col']=='project_id':
                        col['value'] = int(col['value'])
                        col['col']='project'

        except Exception as e:
            print(e)
        return req_json



    @pysnooper.snoop()
    def pre_add(self,item):

        if not item.create_time:
            item.create_time= datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if item.is_fallback==True:
            fallback_version = db.session.query(Embedding).filter(Embedding.project==item.project).filter(Embedding.model_name==item.model_name).filter(Embedding.is_fallback==True).first()
            if fallback_version:
                raise Exception('exist fallback version')

        same_version = db.session.query(Embedding).filter(Embedding.project == item.project).filter(Embedding.model_name == item.model_name).filter(Embedding.version == item.version).first()
        if same_version:
            raise Exception('exist same version')


    def post_update(self,item):
        if item.is_fallback:
            other_fallback_version = db.session.query(Embedding).filter(Embedding.project==item.project).filter(Embedding.model_name == item.model_name).filter(Embedding.version !=item.version).filter(Embedding.is_fallback == True).first()
            other_fallback_version.is_fallback=False
            db.session.commit()
            flash('兜底版本已切换到当前版本%s'%item.version,'success')





    # @pysnooper.snoop()
    def pre_delete(self,item):
        if item.status=='online':
            flash('online version not delete','warning')
            raise Exception('online version not delete')
        if item.is_fallback==True:
            flash('fallback version not delete', 'warning')
            raise Exception('fallback version not delete')
        # exist_item = db.session.query(Embedding).filter(Embedding.model_name==item.model_name).filter(Embedding.id==item.id).all()
        # if not exist_item:
        #     self.delete_deploy(item)


        self.delete_deploy_version(item)


    @expose("/deploy/check_service/<model_id>", methods=["GET",'POST'])
    @pysnooper.snoop()
    def check_service(self,model_id):
        embedding = db.session.query(Embedding).filter_by(id=model_id).first()
        if embedding.status=='online':
            try:
                if embedding.project.expand:
                    l5 = json.loads(embedding.project.expand).get("l5",'')
                    if l5:
                        message = 'model server: '

                        from myapp.utils.jce.rec_ranking_client import REC_RANKING_Client
                        rec_ranking_client = REC_RANKING_Client(l5)
                        result = rec_ranking_client.query_deploy_status(model_name=embedding.model_name)
                        status='success'
                        for ip in result:
                            if message!="model server: ":
                                message+=','
                            res = result[ip]
                            if res and type(res) == str:
                                res = json.loads(res)
                            version = res.get('onlineVersion', '未知')
                            if version != embedding.version:
                                status='warning'
                            message+=ip+"当前版本："+version

                        flash(message,status)

                    else:
                        flash('model server: 未发现%s项目下model server的l5信息' % embedding.project.name,'warning')
                else:
                    flash('model server: 未发现%s项目下model server的l5信息'%embedding.project.name,'warning')
            except Exception as e:
                print(e)
                flash('model server: ' + str(e),'warning')

            try:
                data = {
                    "project": embedding.project.name,
                    "model_name": embedding.model_name
                }
                res = self.post_ef('getModelCurVer',data)
                if res.status_code == 200:
                    print(res.json())
                    result = res.json().get('music.ai.EFIndexSvr.getModelCurVer',{})
                    code = int(result.get('code',1))
                    version = result.get('data',{}).get('version','未知')
                    if code==0:
                        if version==embedding.version:
                            flash('ef server: 当前版本：'+version,'success')
                        else:
                            flash('ef server: ' + json.dumps(result.get("data",{})), 'warning')
                    else:
                        flash('ef server: '+json.dumps(result),'warning')
                else:
                    flash('ef server: ' + str(res.content, encoding='utf-8'), 'warning')
            except Exception as e:
                print(e)
                flash('ef server: ' + str(e),'warning')
        else:
            flash("%s服务未上线"%(embedding.project.name+embedding.model_name+embedding.version,),'warning')
        # 获取model 服务的l5下面每个服务的状态，还有ef下面每个服务的状态
        return redirect('/embedding_modelview/list/')


    @expose("/deploy/prod/<model_id>", methods=["GET",'POST'])
    @pysnooper.snoop()
    def deploy_prod(self,model_id):
        embedding = db.session.query(Embedding).filter_by(id=model_id).first()
        # 通过七彩石部署
        self.deploy(embedding)
        # 更新版本状态
        embedding.status='online'
        # 同名的模型online状态全部变为offline
        same_embeddings= db.session.query(Embedding).filter_by(model_name=embedding.model_name).all()
        for same_embedding in same_embeddings:
            if same_embedding.id!=embedding.id and same_embedding.status=='online':
                same_embedding.status='offline'
        db.session.commit()
        # push_admin('\nuser: %s\nembedding: %s模型部署生产环境' % (embedding.created_by.username, embedding.model_name))
        return redirect('/embedding_modelview/list/')




class Embedding_ModelView(Embedding_ModelView_Base,MyappModelView,DeleteMixin):
    datamodel = SQLAInterface(Embedding)

# 添加视图和菜单
appbuilder.add_view(Embedding_ModelView,"Embedding管理",icon = 'fa-shopping-basket',category = '服务化',category_icon = 'fa-tasks')


# 添加api
class Embedding_ModelView_Api(Embedding_ModelView_Base,MyappModelRestApi):  # noqa
    datamodel = SQLAInterface(Embedding)
    # base_order = ('id', 'desc')
    route_base = '/embedding_modelview/api'
    list_columns=['model_name','version','describe','pipeline','model_path','metrics','embedding_file_path','is_fallback','status','modified']
    add_columns = ['project','pipeline','model_name','version','is_fallback','model_path','embedding_file_path','run_id','metrics']
    edit_columns = add_columns

appbuilder.add_api(Embedding_ModelView_Api)




