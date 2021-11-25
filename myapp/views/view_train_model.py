from flask import render_template,redirect
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask import Blueprint, current_app, jsonify, make_response, request
# 将model添加成视图，并控制在前端的显示
from myapp.models.model_serving import Service
from myapp.models.model_train_model import Training_Model,Training_Model_Deploy
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
from myapp.models.model_job import Repository,Pipeline
from myapp.project import push_message,push_admin
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
    json_response

)
from sqlalchemy import and_, or_, select
from .baseApi import (
    MyappModelRestApi
)

from flask_appbuilder import CompactCRUDMixin, expose
import pysnooper,datetime,time,json
conf = app.config
MODEL_SERVICE_TEST_HOST='11.181.120.155:8081'

class Training_Model_Filter(MyappFilter):
    # @pysnooper.snoop()
    def apply(self, query, func):
        user_roles = [role.name.lower() for role in list(self.get_user_roles())]
        if "admin" in user_roles:
            return query
        return query.filter(self.model.created_by_fk == g.user.id)



# 定义数据库视图
# class Training_Model_ModelView(JsonResModelView,DeleteMixin):
class Training_Model_ModelView_Base():

    datamodel = SQLAInterface(Training_Model)
    base_permissions = ['can_add', 'can_edit', 'can_delete', 'can_list', 'can_show']  # 默认为这些
    base_order = ('changed_on', 'desc')
    order_columns = ['id']
    list_columns = ['name','project_url','pipeline_url','version','creator','status','modified','test_deploy','check_test_service','prod_deploy']
    add_columns = ['project','name','describe','path','framework','status','api_type']
    edit_columns = add_columns
    # add_exclude_columns = ['created_on','changed_on','created_by','changed_by']
    # edit_exclude_columns = add_exclude_columns
    # edit_columns = add_columns
    label_title = '模型'
    base_filters = [["id", Training_Model_Filter, lambda: []]]  # 设置权限过滤器
    help_url = conf.get('HELP_URL', {}).get(datamodel.obj.__tablename__, '') if datamodel else ''

    path_describe= r'''
            不修改，可以不上传。模型压缩文件，仅支持zip 文件类型，英文、数字、- 组成。压缩文件名和解压后文件夹名需保持一致，例如：putoo_deepfm_20210331目录压缩为putoo_deepfm_20210331.zip。<br>
            目录结构规范：<br>
            |-- $your_model_name <br>
            |-- |-- online <br>
            |-- |-- |-- saved_model.pb <br>
            |-- |-- |-- model_desc.xml <br>
            |-- |-- |-- ... <br>
            '''



    def filter_project():
        query = db.session.query(Project)
        user_roles = [role.name.lower() for role in list(get_user_roles())]
        if "admin" in user_roles:
            return query.filter(Project.type=='model').order_by(Project.id.desc())

        # 查询自己拥有的项目
        my_user_id = g.user.get_id() if g.user else 0
        owner_ids_query = db.session.query(Project_User.project_id).filter(Project_User.user_id == my_user_id)

        return query.filter(Project.id.in_(owner_ids_query)).filter(Project.type=='model').order_by(Project.id.desc())



    add_form_extra_fields={

        "project": QuerySelectField(
            _('模型服务项目组'),
            description=_('如果没有可选项目组，可联系管理员加入到项目组中'),
            query_factory=filter_project,
            allow_blank=False,
            widget=Select2Widget()
        ),
        "path": FileField(
            _('模型压缩文件'),
            description=_(path_describe),
            validators=[
                FileRequired(),FileAllowed(["zip",'tar.gz'],_("zip/tar.gz Files Only!")),
            ]
        ),
        "version": StringField(
            _('版本'),
            widget=MyBS3TextFieldWidget(),
            description='模型版本',
            default='v1',
            validators=[DataRequired()]
        ),
        "run_id":StringField(
            _(datamodel.obj.lab('run_id')),
            widget=MyBS3TextFieldWidget(),
            description='pipeline 训练的run id',
            default='random_run_id_'+uuid.uuid4().hex[:32]
        ),
        "name":StringField(
            _("模型名"),
            widget=MyBS3TextFieldWidget(),
            description='模型名(a-z0-9-_字符组成，最长54个字符)需要与压缩文件名(不含扩展格式)和解压后一级目录一致。例如：putoo_deepfm_20210331目录、putoo_deepfm_20210331.zip、模型名为putoo_deepfm_20210331',
            validators = [DataRequired(),Regexp("^[a-z0-9\-_]*$"),Length(1,54)]
        ),
        "framework": SelectField(
            _('算法框架'),
            description="选项tf、xgb、pytorch等",
            widget=Select2Widget(),
            choices=[['tf', 'tf'], ['xgb', 'xgb'], ['pytorch', 'pytorch']]
        ),
        "api_type":SelectField(
            _('接口类型'),
            description="选项Predict、PreditByFloat等",
            widget=Select2Widget(),
            choices=[['Predict', 'Predict'], ['PreditByFloat', 'PreditByFloat']]
        ),
    }
    edit_form_extra_fields=add_form_extra_fields
    edit_form_extra_fields['path']=FileField(
            _('模型压缩文件'),
            description=_(path_describe),
            validators=[
                FileAllowed(["zip",'tar.gz'],_("zip/tar.gz Files Only!")),
            ]
        )


    @pysnooper.snoop(watch_explode=('item'))
    def pre_add(self,item):

        if not item.run_id:
            item.run_id='random_run_id_'+uuid.uuid4().hex[:32]

        # 将模型归档的地方
        archives_host_dir = conf.get('GLOBAL_PVC_MOUNT')['kubeflow-archives'][0]
        archives_container_dir = conf.get('GLOBAL_PVC_MOUNT')['kubeflow-archives'][1]
        if item.pipeline:
            model_dir = os.path.join(item.created_by.username if item.created_by else g.user.username,'%s-%s' % (str(item.pipeline.id), item.pipeline.name), item.run_id)
        else:
            model_dir = os.path.join(item.created_by.username if item.created_by else g.user.username, 'tf-go',item.run_id)

        db_save_path = os.path.join(archives_container_dir, model_dir)

        # 这样可以实现先创建记录再notebook移动数据
        if type(item.path) != FileStorage and not item.path:
            item.path = os.path.join(db_save_path, item.name)
        if type(item.path) == FileStorage:
            try:
                host_save_dir = os.path.join(archives_host_dir, model_dir)
                # 先把目录删除了
                try:
                    if os.path.exists(host_save_dir):
                        shutil.rmtree(host_save_dir)
                except Exception as e:
                    print(e)
                if not os.path.exists(host_save_dir):
                    os.makedirs(host_save_dir)

                host_save_path = os.path.join(host_save_dir,item.path.filename)

                item.path.save(host_save_path)

                zip_file_name=item.path.filename[:item.path.filename.index('.')]

                if zip_file_name!=item.name:
                    raise MyappException('检测到模型名与模型文件不相同')
                db_save_path = os.path.join(db_save_path, zip_file_name)
                print(db_save_path)

                # 检测文件目录是否符合规范
                print(host_save_dir)
                print(host_save_path)
                shutil.unpack_archive(host_save_path,extract_dir=host_save_dir)     # 直接解压成文件夹。数据库里面只保存文件夹目录，不再有压缩文件
                os.remove(host_save_path)   # 直接把压缩文件删除了。用户也可以直接在notebook里面再修改
                if not os.path.exists(os.path.join(host_save_dir,zip_file_name,'online/saved_model.pb')):
                    shutil.rmtree(host_save_dir)
                    error_message = '压缩文件目录结构不符合规范：未找到%s/online/saved_model.pb'%zip_file_name
                    raise MyappException(error_message)
                elif not os.path.exists(os.path.join(host_save_dir,zip_file_name,'online/model_desc.xml')):
                    shutil.rmtree(host_save_dir)
                    error_message = '压缩文件目录结构不符合规范：未找到%s/online/model_desc.xml'%zip_file_name
                    raise MyappException(error_message)
                else:
                    pass


            except MyappException as e1:
                logging.error(e1)
                raise e1
            except Exception as e:
                logging.error(e)
                raise MyappException(str(e))

            item.path = os.path.join(db_save_path,'online')

    def pre_update(self,item):
        if not item.path:
            item.path=self.src_item_json['path']
        self.pre_add(item)

    def post_update(self,item):
        if item.status=='delete':
            self.delete_deploy(item.id)

    def pre_delete(self,item):
        # 删除测试环境
        self.delete_deploy(item.id)

    # 复制模型文件
    @pysnooper.snoop()
    def deploy(self,train_model,des_dir):
        if not os.path.exists(des_dir):
            os.makedirs(des_dir)
        model_path = train_model.path
        archives_host_dir, archives_container_dir = conf.get('GLOBAL_PVC_MOUNT')['kubeflow-archives'][0], conf.get('GLOBAL_PVC_MOUNT')['kubeflow-archives'][1]
        host_model_path = os.path.join(archives_host_dir, model_path.replace(archives_container_dir,''))
        print(host_model_path)
        if os.path.exists(host_model_path):
            # 自动注册进来的是文件夹。web界面上传上来的也解压成文件夹了。
            if os.path.isdir(host_model_path):
                if not os.path.exists(os.path.join(host_model_path,"model_desc.xml")):

                    # 针对少注册了一层目录的模型做一下特殊处理
                    if not os.path.exists(os.path.join(host_model_path,'online')):
                        flash('发现%s文件不存在，服务部署失败' % (os.path.join(host_model_path, "model_desc.xml"),), 'warning')
                        return False
                    else:
                        if not os.path.exists(os.path.join(host_model_path, 'online','model_desc.xml')):
                            flash('发现%s文件不存在，服务部署失败' % (os.path.join(host_model_path, "model_desc.xml"),), 'warning')
                            return False
                        else:
                            host_model_path = os.path.join(host_model_path, 'online')

                des_path = os.path.join(des_dir, train_model.name)
                des_saved_model_path = os.path.join(des_path, 'online')

                # copytree需要先删除目目录
                if os.path.exists(des_saved_model_path):
                    shutil.rmtree(des_saved_model_path)

                shutil.copytree(host_model_path, des_saved_model_path)

                flash('%s部署成功，部署目录：%s' % (train_model.name, des_saved_model_path), 'success')
                print(des_saved_model_path)

                return True


        else:
            flash('%s部署失败，%s下当前模型版本文件不存在' % (train_model.name,host_model_path),'warning')
            return False


    # 清理部署文件
    # @pysnooper.snoop()
    def delete_deploy(self,model_id):
        train_model = db.session.query(Training_Model).filter_by(id=model_id).first()
        model_deploy_host_dir, model_deploy_container_dir = conf.get('GLOBAL_PVC_MOUNT')['kubeflow-model-deploy'][0], conf.get('GLOBAL_PVC_MOUNT')['kubeflow-model-deploy'][1]

        try:
            # 状态为生产才能真正删除。不然有online可能还在用可能还在用
            if self.src_item_json['status']=='online' or self.src_item_json['status']=='test':
                test_des_dir = model_deploy_host_dir+"test"

                # 删除测试环境压缩文件
                # test_des_zip_path = os.path.join(test_des_dir, os.path.basename(train_model.path))
                #             # if os.path.exists(test_des_zip_path):
                #             #     if os.path.isdir(test_des_zip_path):
                #             #         shutil.rmtree(test_des_zip_path)
                #             #     if os.path.isfile(test_des_zip_path):
                #             #         os.remove(test_des_zip_path)
                # 删除测试环境目录
                test_des_path = os.path.join(test_des_dir, train_model.name)
                if os.path.exists(test_des_path):
                    # 直接删除
                    # if os.path.isdir(test_des_path):
                    #     shutil.rmtree(test_des_path)
                    # if os.path.isfile(test_des_path):
                    #     os.remove(test_des_path)

                    # 写删除命令文件
                    delete_comman_file = os.path.join(test_des_path,'online')
                    if os.path.exists(delete_comman_file):
                        file = open(delete_comman_file+"/model.delete",mode='w')
                        file.write('')
                        file.close()

            if self.src_item_json['status'] == 'online':
                prod_des_dir = model_deploy_host_dir + "product/"
                if train_model.project:
                    prod_des_dir +=train_model.project.name
                elif train_model.pipeline.project:
                    prod_des_dir += train_model.pipeline.project.name

                # 删除生产环境压缩文件
                # prod_des_zip_path = os.path.join(prod_des_dir, os.path.basename(train_model.path))
                # if os.path.exists(prod_des_zip_path):
                #     if os.path.isdir(prod_des_zip_path):
                #         shutil.rmtree(prod_des_zip_path)
                #     if os.path.isfile(prod_des_zip_path):
                #         os.remove(prod_des_zip_path)

                # 删除生产环境目录
                prod_des_path = os.path.join(prod_des_dir, train_model.name)
                if os.path.exists(prod_des_path):
                    # 直接删除
                    # if os.path.isdir(prod_des_path):
                    #     shutil.rmtree(prod_des_path)
                    # if os.path.isfile(prod_des_path):
                    #     os.remove(prod_des_path)

                    # 写删除命令文件
                    delete_comman_file = os.path.join(prod_des_path,'online')
                    if os.path.exists(delete_comman_file):
                        file = open(delete_comman_file+"/model.delete",mode='w')
                        file.write('')
                        file.close()

        except Exception as e:
            flash(str(e),'warning')
        push_admin('\nuser: %s\nmodel: %s模型服务下线\nstatus: 下线前状态%s' % (train_model.created_by.username, train_model.name,self.src_item_json['status']))
        push_message([train_model.created_by.username],'model: %s模型服务下线\nstatus: 下线前状态%s'%(train_model.name,self.src_item_json['status']))
        return redirect('/training_model_modelview/list/')


    @expose("/deploy/test/<model_id>", methods=["GET",'POST'])
    def deploy_test(self,model_id):
        train_model = db.session.query(Training_Model).filter_by(id=model_id).first()
        model_deploy_host_dir, model_deploy_container_dir = conf.get('GLOBAL_PVC_MOUNT')['kubeflow-model-deploy'][0], conf.get('GLOBAL_PVC_MOUNT')['kubeflow-model-deploy'][1]
        des_dir = model_deploy_host_dir+"test"
        self.deploy(train_model, des_dir=des_dir)

        # 同名的模型test状态全部变为offline
        same_train_models= db.session.query(Training_Model).filter_by(name=train_model.name).all()
        for same_train_model in same_train_models:
            if same_train_model.id!=train_model.id and same_train_model.status=='test':
                same_train_model.status='offline'
        db.session.commit()

        message = '\nuser: %s\nmodel: %s模型部署测试环境\nmetric:%s'%(train_model.created_by.username,train_model.name,train_model.metrics)
        push_admin(message)
        push_message([train_model.created_by.username],message)
        return redirect('/training_model_modelview/list/')


    @expose("/deploy/check_test/<model_id>", methods=["GET",'POST'])
    def check_test(self,model_id):
        train_model = db.session.query(Training_Model).filter_by(id=model_id).first()
        res = requests.get('http://%s/predict_test?modelName=%s&version=%s'%(MODEL_SERVICE_TEST_HOST,train_model.name,'v2' if train_model.api_type and train_model.api_type=='PreditByFloat' else "v1"))
        flash('响应：'+str(res.content),category='warning')
        # if 'success' in str(res.content):
        #     train_model.status = 'test'
        #     db.session.commit()
        return redirect('/training_model_modelview/list/')


    @expose("/deploy/prod/<model_id>", methods=["GET",'POST'])
    def deploy_prod(self,model_id,force=False):
        train_model = db.session.query(Training_Model).filter_by(id=model_id).first()

        if not force:
            if train_model.status != 'test':
                flash('test状态的模型才能部署到生产。若已检测测试服务正常，可手动编辑模型状态为test，并保证项目组正确', category='warning')
                return redirect('/training_model_modelview/edit/%s' % model_id)

        if not train_model.project or train_model.project.type!='model':
            flash('项目组不正确，请先修改项目组为该模型所属项目',category='warning')
            return redirect('/training_model_modelview/edit/%s'%model_id)

        model_deploy_host_dir, model_deploy_container_dir = conf.get('GLOBAL_PVC_MOUNT')['kubeflow-model-deploy'][0], \
                                                            conf.get('GLOBAL_PVC_MOUNT')['kubeflow-model-deploy'][1]
        des_dir = model_deploy_host_dir + "product/"
        if train_model.project:
            des_dir += train_model.project.name
        elif train_model.pipeline.project:
            des_dir += train_model.pipeline.project.name

        self.deploy(train_model, des_dir=des_dir)
        train_model.status = 'online'

        # 同名的模型online状态全部变为offline
        same_train_models = db.session.query(Training_Model).filter_by(name=train_model.name).all()
        for same_train_model in same_train_models:
            if same_train_model.id != train_model.id and same_train_model.status == 'online':
                same_train_model.status = 'offline'
        db.session.commit()
        message='\nuser: %s\nmodel: %s模型部署生产环境\nmetric:%s' % (train_model.created_by.username, train_model.name,train_model.metrics)
        push_admin(message)
        push_message([train_model.created_by.username],message)

        return redirect('/training_model_modelview/list/')

    @expose("/api/deploy/<env>", methods=["GET", 'POST'])
    @pysnooper.snoop()
    def api_deploy(self,env):
        try:
            model_project_name = request.json.get('model_project_name', '')
            pipeline_id = int(request.json.get('pipeline_id', '0'))
            run_id = request.json.get('run_id', '')
            model_path = request.json.get('model_path', '')
            model_name = request.json.get('model_name', '')
            model_project = db.session.query(Project).filter_by(name=model_project_name).filter_by(type='model').first()
            train_model=None
            if pipeline_id and run_id:
                # pipeline = db.session.query(Pipeline).filter_by(id=pipeline_id).first()
                train_model = db.session.query(Training_Model).filter_by(pipeline_id=pipeline_id).filter_by(run_id=run_id).first()
            elif model_path and model_name:
                train_model = db.session.query(Training_Model).filter_by(path=model_path).filter_by(name=model_name).first()

            if train_model and env in ['test','prod']:
                if env=='test':
                    self.deploy_test(train_model.id)
                    return json_response(message='deploy %s success' % env, status=0, result={})
                elif env=='prod' and model_project:
                    train_model.project=model_project
                    db.session.commit()
                    self.deploy_prod(train_model.id,force=True)
                    return json_response(message='deploy %s success'%env,status=0,result={})


            return json_response(message='no pipeline, run_id, model_project or env not in test,prod',status=1,result={})
        except Exception as e:
            return json_response(message=str(e),status=1,result={})



    # @event_logger.log_this
    @action("muldelete", "Delete", "Delete all Really?", "fa-rocket", single=False)
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect())


    # @event_logger.log_this
    @action('download','Download','下载模型会先压缩整个path目录成zip，时间可能耗时较久','fa-download',single=True,multiple=False)
    def download(self,train_model):

        # # 打包目录为zip文件（未压缩）
        # def make_zip(source_dir, output_filename):
        #     zipf = zipfile.ZipFile(output_filename, 'w')
        #     pre_len = len(os.path.dirname(source_dir))
        #     for parent, dirnames, filenames in os.walk(source_dir):
        #         for filename in filenames:
        #             pathfile = os.path.join(parent, filename)
        #             arcname = pathfile[pre_len:].strip(os.path.sep)  # 相对路径
        #             zipf.write(pathfile, arcname)
        #     zipf.close()


        model_path = train_model.path
        archives_host_dir, archives_container_dir = conf.get('GLOBAL_PVC_MOUNT')['kubeflow-archives'][0], conf.get('GLOBAL_PVC_MOUNT')['kubeflow-archives'][1]
        host_model_path = os.path.join(archives_host_dir, model_path.replace(archives_container_dir,''))
        print(host_model_path)
        if os.path.exists(host_model_path):
            parent_dir = os.path.dirname(host_model_path)
            zip_file_name = os.path.basename(host_model_path)
            if os.path.isfile(host_model_path):
                pass
            if os.path.isdir(host_model_path):
                zip_dir = os.path.basename(host_model_path)
                zip_file_name = train_model.name+".zip"
                des_path = os.path.join(parent_dir, train_model.name)
                des_path_zip = os.path.join(parent_dir,zip_file_name)
                if os.path.exists(des_path_zip):
                    os.remove(des_path_zip)
                # 压缩会将当前目录一块压缩了，这样解压的时候就是整个文件夹，而不是文件夹内的内容
                shutil.make_archive(base_name=des_path,format='zip',root_dir=parent_dir,base_dir=zip_dir)

            response = make_response(send_from_directory(parent_dir, zip_file_name, as_attachment=True, conditional=True))

            response.headers[
                "Content-Disposition"
            ] = f"attachment; filename={zip_file_name}"
            logging.info("Ready to return response")
            return response
        else:
            flash('store path not exist',category='warning')
            return redirect('/training_model_modelview/show/%s'%str(train_model.id))


class Training_Model_ModelView(Training_Model_ModelView_Base,MyappModelView,DeleteMixin):
    datamodel = SQLAInterface(Training_Model)

# 添加视图和菜单
appbuilder.add_view(Training_Model_ModelView,"模型管理",icon = 'fa-shopping-basket',category = '服务化',category_icon = 'fa-tasks')


# 添加api
class Training_Model_ModelView_Api(Training_Model_ModelView_Base,MyappModelRestApi):  # noqa
    datamodel = SQLAInterface(Training_Model)
    # base_order = ('id', 'desc')
    route_base = '/training_model_modelview/api'
    list_columns=['name','version','describe','pipeline','path','status','metrics','modified']
    add_columns = ['pipeline','name','version','describe','path','framework','download_url','run_id','run_time','metrics','md5','status']
    edit_columns = add_columns

appbuilder.add_api(Training_Model_ModelView_Api)




class Training_Model_Deploy_Filter(MyappFilter):
    # @pysnooper.snoop()
    def apply(self, query, func):
        user_roles = [role.name.lower() for role in list(self.get_user_roles())]
        if "admin" in user_roles:
            return query.order_by(self.model.id.desc())
        return query.filter(self.model.created_by_fk == g.user.id).order_by(self.model.id.desc())


# 定义数据库视图
class Training_Model_Deploy_ModelView(MyappModelView,DeleteMixin):   # JsonResModelView
    datamodel = SQLAInterface(Training_Model_Deploy)
    base_permissions = ['can_add', 'can_edit', 'can_delete', 'can_list', 'can_show']  # 默认为这些
    base_order = ('id', 'desc')
    order_columns = ['id']
    list_columns = ['model_name','pipeline','run_id','ip','deploy_time']
    # add_columns = ['name','version','describe','workflow_id','pvc_path','download_url','ext']
    add_exclude_columns = ['created_on','changed_on','created_by','changed_by']
    edit_exclude_columns = add_exclude_columns
    # edit_columns = add_columns
    label_title = '模型部署'
    base_filters = [["id", Training_Model_Deploy_Filter, lambda: []]]  # 设置权限过滤器
    # label_columns = {
    #     "model_name": _("模型"),
    #     "pipeline": _("任务流"),
    #     "deploy_time": _("部署时间")
    # }

# 添加视图和菜单
# appbuilder.add_view(Training_Model_Deploy_ModelView,"部署机器",icon = 'fa-shopping-basket',category = '服务化',category_icon = 'fa-tasks')


# 添加api
class Training_Model_Deploy_ModelView_Api(MyappModelRestApi):  # noqa
    datamodel = SQLAInterface(Training_Model_Deploy)
    base_order = ('id', 'desc')
    route_base = '/training_model_deploy_modelview/api'

    # @event_logger.log_this
    @expose('/deploy',methods=['POST'])
    def deploy(self):
        try:
            data = request.json or {}
            pipeline_id = int(data.get('pipeline_id'))
            run_id = data.get('run_id')
            ip = data.get('ip')
            status=data.get('status')
            deploy_time = data.get('deploy_time')
            train_model = db.session.query(Training_Model).filter_by(pipeline_id=pipeline_id,run_id=run_id).first()
            if train_model:
                if train_model.status=='offline':
                    train_model.status='online'
                model_deploy = Training_Model_Deploy(ip=ip,status=status,deploy_time=deploy_time,train_model=train_model)
                db.session.add(model_deploy)
                db.session.commit()
                back={
                    "message":"success",
                    "status":0,
                    "result":model_deploy.to_json()
                }
                return jsonify(back)
            return jsonify({
                "message": "train model not exist, request json is %s"%json.dumps(data),
                "status": 1,
                "result": {}
            })
        except Exception as e:
            return jsonify({
                "message": str(e),
                "status": 1,
                "result": {}
            })


appbuilder.add_api(Training_Model_Deploy_ModelView_Api)
