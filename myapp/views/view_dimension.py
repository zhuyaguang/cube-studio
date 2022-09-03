import traceback

from flask import render_template,redirect
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi
from flask_appbuilder import ModelView,AppBuilder,expose,BaseView,has_access
from importlib import reload
from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
from flask_babel import lazy_gettext,gettext
from flask_appbuilder.forms import GeneralModelConverter
from flask import current_app, flash, jsonify, make_response, redirect, request, url_for
import uuid
import copy
import random
from sqlalchemy.exc import SQLAlchemyError,InvalidRequestError
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Blueprint, current_app, jsonify, make_response, request
from flask_appbuilder.actions import action
import re,os
from sqlalchemy import and_, or_, select
from wtforms.validators import DataRequired, Length, NumberRange, Optional,Regexp
from kfp import compiler

from myapp import app, appbuilder,db,event_logger
from myapp.utils import core
from wtforms import BooleanField, IntegerField,StringField, SelectField,FloatField,DateField,DateTimeField,SelectMultipleField,FormField,FieldList
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget,BS3PasswordFieldWidget,DatePickerWidget,DateTimePickerWidget,Select2ManyWidget,Select2Widget
from myapp.forms import MyBS3TextAreaFieldWidget,MySelect2Widget,MyCodeArea,MyLineSeparatedListField,MyJSONField,MyBS3TextFieldWidget,MySelectMultipleField,MySelect2ManyWidget
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask_appbuilder.api.convert import Model2SchemaConverter
from .baseApi import (
    MyappModelRestApi,
    json_response
)
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
from myapp import security_manager
from werkzeug.datastructures import FileStorage
from .base import (
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
)
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from myapp.models.model_dimension import Dimension_table
from flask_appbuilder import CompactCRUDMixin, expose
import pysnooper,datetime,time,json
from myapp.security import MyUser
conf = app.config
logging = app.logger



class Dimension_table_Filter(MyappFilter):
    # @pysnooper.snoop()
    def apply(self, query, func):
        if g.user.is_admin():
            return query.filter(self.model.status==1)

        return query.filter(self.model.status==1).filter(
            or_(
                self.model.owner.contains(g.user.username),
                self.model.owner.contains('*'),
            )
        )


Metadata_column_fields = {
    "name":StringField(
        label=_("列名"),
        description='列名(小写字母、数字、_ 组成)，最长50个字符',
        default='',
        widget=BS3TextFieldWidget(),
        validators=[Regexp("^[a-z][a-z0-9_]*[a-z0-9]$"), Length(1, 54),DataRequired()]
    ),
    "describe": StringField(
        label=_('列描述'),
        description='列名描述',
        default='',
        widget=BS3TextFieldWidget(),
        validators=[DataRequired()]
    ),
    "column_type": SelectField(
        label=_('字段类型'),
        description='列类型',
        widget=Select2Widget(),
        default='text',
        choices=[['int', 'int'], ['text', 'text'],['date', 'date']],
        validators=[DataRequired()]
    ),
    "unique": BooleanField(
        label=_('是否唯一'),
        description='是否唯一',
        default=False,
        widget=BS3TextFieldWidget(),
    ),
    "nullable": BooleanField(
        label=_('是否可为空'),
        description='是否可为空',
        default=True,
        widget=BS3TextFieldWidget(),
    ),
    "primary_key": BooleanField(
        label=_('是否为主键'),
        description='是否为主键',
        default=False,
        widget=BS3TextFieldWidget(),
    )
}

from myapp.project import push_message, push_admin


@pysnooper.snoop()
def ddl_hive_external_table(table_id):
    username = g.user.username

    try:
        item = db.session.query(Dimension_table).filter_by(id=int(table_id)).first()
        if not item:
            return
        cols = json.loads(item.columns)
        # 创建hive外表
        hive_type_map = {'INT': 'INT', 'TEXT': 'STRING', 'STRING': 'STRING', 'DATE': 'STRING'}
        cols_lst = []
        for col_name in cols:
            if col_name in ['id',]:
                continue
            column_type = cols[col_name].get('column_type', 'text').upper()
            if column_type not in hive_type_map:
                raise RuntimeError("更新了不支持新字段类型")
            column_type = hive_type_map[column_type]
            col_str = col_name + ' ' + column_type
            cols_lst.append(col_str)

        columns_sql = ',\n'.join(cols_lst).strip(',')
        import sqlalchemy.engine.url as url
        uri = url.make_url(item.sqllchemy_uri)
        hive_sql = ''' 
# hive建外表
CREATE EXTERNAL TABLE IF NOT EXISTS {table_name}  (
id BIGINT,
{columns_sql}
) 
with (ip='{ip}',port='{port}',db_name='{pg_db_name}',user_name='{user_name}',pwd='{password}',table_name='{pg_table_name}',charset='utf8',db_type='pg');

                        '''.format(
            table_name=item.table_name,
            columns_sql=columns_sql,
            ip=uri.host,
            port=str(uri.port),
            user_name=uri.username,
            password=uri.password,
            pg_db_name=uri.database,
            pg_table_name=item.table_name
        )
        return hive_sql
    except Exception as e:
        print(e)
        return str(e)


class Dimension_table_ModelView_Api(MyappModelRestApi):
    datamodel = SQLAInterface(Dimension_table)
    label_title = '维表'
    route_base = '/dimension_table_modelview/api'
    base_permissions = ['can_add','can_list','can_delete','can_show','can_edit']
    add_columns = ['sqllchemy_uri','app','table_name','label','describe','owner','columns']
    edit_columns = add_columns
    show_columns = ['id','app','sqllchemy_uri','label','describe','table_name','owner','columns','status']
    search_columns=['id','app','table_name','label','describe','sqllchemy_uri']
    order_columns = ['id']
    base_order = ('id', 'desc')
    list_columns = ['table_html','label','owner','describe','operate_html']
    cols_width = {
        "table_html":{"type": "ellip2", "width": 300},
        "label":{"type": "ellip2", "width": 300},
        "owner": {"type": "ellip2", "width": 300},
        "describe": {"type": "ellip2", "width": 300},
        "operate_html":{"type": "ellip2", "width": 400}
    }
    spec_label_columns = {
        "sqllchemy_uri":"链接串地址",
        "owner":"负责人",
        "columns": "列信息",
        "table_html":"表名",
        "table_name":"表名"
    }
    base_filters = [["id", Dimension_table_Filter, lambda: []]]

    add_fieldsets = [
        (
            lazy_gettext('表元数据'),
            {"fields": ['sqllchemy_uri','app','table_name','label','describe','owner'], "expanded": True},
        ),
        (
            lazy_gettext('列信息'),
            {"fields": ['columns'],
             "expanded": True},
        )
    ]
    edit_fieldsets = add_fieldsets

    add_form_extra_fields = {
        "sqllchemy_uri":StringField(
            _(datamodel.obj.lab('sqllchemy_uri')),
            default="",
            description='链接串地址： <br> mysql+pymysql://root:admin@host.docker.internal:3306/db_name?charset=utf8 <br> postgresql+psycopg2://root:admin@host.docker.internal:5432/db_name',
            widget=BS3TextFieldWidget(),
            validators=[DataRequired(),Regexp("^(mysql\+pymysql|postgresql\+psycopg2)")]
        ),
        "table_name":StringField(
            label=_(datamodel.obj.lab('table_name')),
            description='远程数据库的表名',
            widget=BS3TextFieldWidget(),
            default='',
            validators=[DataRequired(),Regexp("^[a-z][a-z0-9_\-]*[a-z0-9]$")]
        ),
        "label": StringField(
            label=_(datamodel.obj.lab('label')),
            description='中文名',
            widget=BS3TextFieldWidget(),
            default='',
            validators=[DataRequired()]
        ),
        "describe": StringField(
            label=_(datamodel.obj.lab('describe')),
            description='描述',
            widget=BS3TextFieldWidget(),
            default='',
            validators=[DataRequired()]
        ),
        "app":SelectField(
            label=_(datamodel.obj.lab('app')),
            description='产品分类',
            widget=MySelect2Widget(can_input=True,conten2choices=True),
            default='',
            choices=[[x,x] for x in ['产品1',"产品2","产品3"]],
            validators=[DataRequired()]
        ),
        "owner": StringField(
            label=_(datamodel.obj.lab('owner')),
            default='',
            description='责任人,逗号分隔的多个用户',
            widget=BS3TextFieldWidget(),
            validators=[DataRequired()]
        ),

    }
    edit_form_extra_fields = add_form_extra_fields

    @pysnooper.snoop()
    def pre_add(self, item):
        if not item.columns:
            item.columns='{}'
        # 如果没有主键列就自动加上主键列
        cols = json.loads(item.columns)
        primary_col=''
        for col_name in cols:
            if cols[col_name].get('primary_key',False):
                primary_col=col_name
        if not primary_col:
            cols['id']= {
                "column_type": "int",
                "describe": "主键",
                "name": "id",
                "nullable": False,
                "primary_key": True,
                "unique": True
            }
            item.columns=json.dumps(cols,indent=4,ensure_ascii=False)

        if not item.owner or g.user.username not in item.owner:
            item.owner = g.user.username if not item.owner else item.owner + "," + g.user.username

    def pre_update(self, item):
        if not item.sqllchemy_uri:
            item.sqllchemy_uri=self.src_item_json.get('sqllchemy_uri','')
        self.pre_add(item)


    # 转换为前端list
    def pre_get(self,_response):
        data = _response['data']
        columns=json.loads(data.get('columns','{}'))
        columns_list=[]
        for name in columns:
            col = columns[name]
            col.update({"name":name})
            columns_list.append(col)
        data['columns']=columns_list


    # 将前端columns list转化为字段存储
    def pre_json_load(self, req_json=None):
        if req_json and 'columns' in req_json:
            columns={}
            for col in req_json.get('columns',[]):
                columns[col['name']]=col
            req_json['columns'] = json.dumps(columns,indent=4,ensure_ascii=False)
        return req_json

    # 获取指定维表里面的数据
    @staticmethod
    def get_dim_target_data(dim_id):
        import pandas
        dim = db.session.query(Dimension_table).filter_by(id=int(dim_id)).first()
        import sqlalchemy.engine.url as url
        uri = url.make_url(dim.sqllchemy_uri)
        sql_engine = create_engine(uri)
        columns = list(json.loads(dim.columns).values())
        cols = [col['name'] for col in columns if not col.get('primary_key',False)]
        sql = 'select %s from %s' % (','.join(cols), dim.table_name)
        results = pandas.read_sql_query(sql, sql_engine)
        return results.to_dict()


    @expose("/csv/<dim_id>", methods=["GET"])
    # @pysnooper.snoop()
    def csv(self,dim_id):
        dim = db.session.query(Dimension_table).filter_by(id=int(dim_id)).first()
        cols = json.loads(dim.columns)
        for col_name in copy.deepcopy(cols):
            if cols[col_name].get('primary_key',False):
                del cols[col_name]
        demostr=','.join(list(cols.keys()))+"\n"+','.join(['xx' for x in list(cols.keys())])

        csv_file='%s.csv'%dim_id
        file = open(csv_file,mode='w',encoding='utf-8-sig')
        file.writelines(demostr)
        file.close()
        csv_file = os.path.abspath(csv_file)
        response = self.csv_response(csv_file,file_name=dim.table_name)
        return response
        # return ','.join(list(cols.keys()))+"<br>"+','.join(['xx' for x in list(cols.keys())])

    @expose("/download/<dim_id>", methods=["GET"])
    # @pysnooper.snoop()
    def download(self,dim_id):
        import pandas
        dim = db.session.query(Dimension_table).filter_by(id=int(dim_id)).first()
        import sqlalchemy.engine.url as url
        uri = url.make_url(dim.sqllchemy_uri)
        sql_engine = create_engine(uri)
        columns = list(json.loads(dim.columns).values())
        cols = [col['name'] for col in columns if not col.get('primary_key', False)]
        sql = 'select %s from %s' % (','.join(cols), dim.table_name)
        results = pandas.read_sql_query(sql, sql_engine)
        file_path = '%s.csv' % dim.table_name
        csv_file = os.path.abspath(file_path)
        if os.path.exists(csv_file):
            os.remove(csv_file)
        results.to_csv(csv_file, index=False, sep=",")  # index 是第几行的表示
        response = self.csv_response(csv_file, file_name=dim.table_name)
        return response

    @expose("/external/<dim_id>", methods=["GET"])
    def external(self,dim_id):
        ddl_sql = ddl_hive_external_table(dim_id)
        print(ddl_sql)
        return Markup(ddl_sql.replace('\n','<br>'))

    @expose("/clear/<dim_id>", methods=["GET"])
    def clear(self,dim_id):
        try:
            dim = db.session.query(Dimension_table).filter_by(id=int(dim_id)).first()
            import sqlalchemy.engine.url as url
            uri = url.make_url(dim.sqllchemy_uri)
            engine = create_engine(uri)
            dbsession = scoped_session(sessionmaker(bind=engine))
            dbsession.execute('TRUNCATE TABLE  %s;'%dim.table_name)
            dbsession.commit()
            dbsession.close()
            flash('清空完成','success')
        except Exception as e:
            flash('清空失败：'+str(e), 'error')

        url_path = conf.get('MODEL_URLS', {}).get("dimension")+'?targetId='+dim_id
        return redirect(url_path)




    @expose("/create_external_table/<dim_id>", methods=["GET"])
    # @pysnooper.snoop()
    def create_external_table(self, dim_id):
        item = db.session.query(Dimension_table).filter_by(id=int(dim_id)).first()
        sqllchemy_uri = item.sqllchemy_uri
        if sqllchemy_uri:

            # 创建数据库的sql(如果数据库存在就不创建，防止异常)
            if 'postgresql' in item.sqllchemy_uri:
                # 创建pg表
                import sqlalchemy.engine.url as url
                uri = url.make_url(sqllchemy_uri)
                from sqlalchemy import create_engine
                from sqlalchemy.orm import scoped_session, sessionmaker
                engine = create_engine(uri)
                dbsession = scoped_session(sessionmaker(bind=engine))
                cols = json.loads(item.columns)
                table_schema = 'public'

                import pandas as pd
                read_col_sql = r"select column_name from information_schema.columns where table_schema='%s' and table_name='%s' "%(table_schema,item.table_name)
                print(read_col_sql)
                company_data = pd.read_sql(read_col_sql,con=engine)
                # 如果表不存在
                sql=''
                if company_data.empty:
                    # 如果远程没有表，就建表
                    sql = '''
                    CREATE TABLE if not exists  {table_name}  (
                        id BIGINT PRIMARY KEY,
                        {columns_sql}
                    );
                                    '''.format(
                        table_name=item.table_name,
                        columns_sql='\n'.join(
                            ["    %s %s %s %s," % (col_name, 'BIGINT' if cols[col_name].get('column_type','text').upper() == 'INT' else 'varchar(2000)',
                                                   '' if int(cols[col_name].get('nullable', True)) else 'NOT NULL',
                                                   '' if not int(cols[col_name].get('unique', False)) else 'UNIQUE') for
                             col_name in cols if col_name not in ['id',]]
                        ).strip(',')
                    )
                    # 执行创建数据库的sql
                    print(sql)
                    if sql:
                        dbsession.execute(sql)
                        dbsession.commit()
                    flash('创建新表成功', 'success')
                else:
                    exist_columns=list(company_data.head().to_dict()['column_name'].values())
                    print(exist_columns)
                    if exist_columns:
                        col = json.loads(item.columns)
                        for column_name in col:
                            col_type = 'INT' if col[column_name].get('column_type','text').upper() == 'INT' else 'varchar(2000)'
                            if column_name not in exist_columns:
                                try:
                                    sql = 'ALTER TABLE %s ADD %s %s;'%(item.table_name,column_name,col_type)
                                    print(sql)
                                    dbsession.execute(sql)
                                    dbsession.commit()
                                    flash('增加新字段成功', 'success')
                                except Exception as e:
                                    dbsession.rollback()
                                    print(e)
                                    flash('增加新字段失败：'+str(e), 'error')

                dbsession.close()
                # 如果远程有表，就增加字段


            # 创建数据库的sql(如果数据库存在就不创建，防止异常)
            if 'mysql' in item.sqllchemy_uri:
                # 创建mysql表
                import sqlalchemy.engine.url as url
                uri = url.make_url(sqllchemy_uri)
                from sqlalchemy import create_engine
                from sqlalchemy.orm import scoped_session, sessionmaker
                engine = create_engine(uri)
                dbsession = scoped_session(sessionmaker(bind=engine))
                cols = json.loads(item.columns)

                import sqlalchemy
                try:
                    table = sqlalchemy.Table(item.table_name, sqlalchemy.MetaData(), autoload=True, autoload_with=engine)

                    exist_columns=[str(col).replace(item.table_name,'').replace('.','') for col in table.c]
                    print(exist_columns)
                    if exist_columns:
                        col = json.loads(item.columns)
                        for column_name in col:
                            col_type = 'INT' if col[column_name].get('column_type','text').upper() == 'INT' else 'varchar(2000)'
                            if column_name not in exist_columns:
                                try:
                                    sql = 'ALTER TABLE %s ADD %s %s;'%(item.table_name,column_name,col_type)
                                    print(sql)
                                    dbsession.execute(sql)
                                    dbsession.commit()
                                    flash('增加新字段成功', 'success')
                                except Exception as e:
                                    dbsession.rollback()
                                    print(e)
                                    flash('增加新字段失败：'+str(e), 'error')


                except sqlalchemy.exc.NoSuchTableError as e:
                    print('表不存在')
                    # 如果表不存在

                    # 如果远程没有表，就建表
                    sql = '''
                    CREATE TABLE if not exists  {table_name}  (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        {columns_sql}
                    );
                                    '''.format(
                        table_name=item.table_name,
                        columns_sql='\n'.join(
                            ["    %s %s %s %s," % (col_name, 'BIGINT' if cols[col_name].get('column_type','text').upper() == 'INT' else 'varchar(2000)',
                                                   '' if int(cols[col_name].get('nullable', True)) else 'NOT NULL',
                                                   '' if not int(cols[col_name].get('unique', False)) else 'UNIQUE') for
                             col_name in cols if col_name not in ['id',]]
                        ).strip(',')
                    )
                    # 执行创建数据库的sql
                    print(sql)
                    if sql:
                        dbsession.execute(sql)
                        dbsession.commit()
                        flash('创建新表成功','success')

                dbsession.close()
                # 如果远程有表，就增加字段

        url_path = conf.get('MODEL_URLS', {}).get("dimension")+'?targetId='+dim_id
        return redirect(url_path)


    def add_more_info(self,response,**kwargs):
        from myapp.views.baseApi import API_RELATED_RIS_KEY, API_ADD_COLUMNS_RES_KEY, API_EDIT_COLUMNS_RES_KEY
        for col in response[API_ADD_COLUMNS_RES_KEY]:
            if col['name']=='columns':
                response[API_EDIT_COLUMNS_RES_KEY].remove(col)
        for col in response[API_EDIT_COLUMNS_RES_KEY]:
            if col['name'] == 'columns':
                response[API_EDIT_COLUMNS_RES_KEY].remove(col)

        response[API_ADD_COLUMNS_RES_KEY].append({
            "name": "columns",
            "ui-type": "list",
            "info": self.columnsfield2info(Metadata_column_fields)
        })
        response[API_EDIT_COLUMNS_RES_KEY].append({
            "name": 'columns',
            "ui-type": "list",
            "info": self.columnsfield2info(Metadata_column_fields)
        })


appbuilder.add_api(Dimension_table_ModelView_Api)





from flask_appbuilder import Model
from myapp.models.base import MyappModelBase
from sqlalchemy import Column, Integer, String, ForeignKey, Float,BigInteger,Date
from sqlalchemy.orm import relationship


class Dimension_remote_table_ModelView_Api(MyappModelRestApi):
    datamodel = SQLAInterface(Dimension_table)

    route_base = '/dimension_remote_table_modelview'

    # @pysnooper.snoop()
    def set_model(self,dim_id):

        dim = db.session.query(Dimension_table).filter_by(id=int(dim_id)).first()
        if not dim:
            raise Exception("no dimension")

        all_dimension = conf.get('all_dimension_instance',{})
        if "dimension_%s"%dim_id not in all_dimension:
            columns = json.loads(dim.columns) if dim.columns else {}
            column_class = {}

            spec_label_columns = {}
            search_columns = []
            label_columns={}
            add_columns=[]
            edit_columns=[]
            show_columns=[]
            list_columns=[]
            description_columns={}
            add_form_extra_fields={}
            add_form_query_rel_fields={}
            validators_columns={}
            order_columns=[]
            cols_width = {
            }
            for column_name in columns:
                column_type = columns[column_name].get('column_type','string')
                if column_type == 'int':
                    cols_width[column_type] ={
                        "type": "ellip1",
                        "width": 100
                    }
                if column_type == 'date':
                    cols_width[column_type] ={
                        "type": "ellip1",
                        "width": 200
                    }
                if column_type == 'text':
                    cols_width[column_type] ={
                        "type": "ellip2",
                        "width": 300
                    }

                column_sql_type = BigInteger if column_type == 'int' else String  # 因为实际使用的时候，会在数据库中存储浮点数据，通用性也更强

                val=[DataRequired()] if not columns[column_name].get('nullable',True) else []
                if column_type =='date':
                    column_sql_type=String
                    add_form_extra_fields[column_name] = StringField(
                        _(column_name),
                        default=datetime.datetime.now().strftime('%Y-%m-%d'),
                        description='',  # columns[column_name]['describe'],
                        widget=BS3TextFieldWidget(),
                        validators=[Regexp("^[0-9]{4,4}-[0-9]{2,4}-[0-9]{2,2}$")]+val
                    )
                else:
                    add_form_extra_fields[column_name] = StringField(
                        _(column_name),
                        default='',
                        description='',  # columns[column_name]['describe'],
                        widget=BS3TextFieldWidget(),
                        validators=val
                    )

                column_class[column_name] = Column(
                    column_sql_type,
                    nullable=columns[column_name].get('nullable',True),
                    unique=columns[column_name].get('unique',False),
                    primary_key=columns[column_name].get('primary_key',False)
                )

                spec_label_columns[column_name] = columns[column_name]['describe']

                label_columns[column_name]=columns[column_name]['describe']
                description_columns[column_name] = columns[column_name]['describe']
                add_columns.append(column_name)
                show_columns.append(column_name)
                list_columns.append(column_name)
                if column_type == 'string' or column_type=='text' or column_type=='int':
                    if not int(columns[column_name].get('primary_key',False)):
                        search_columns.append(column_name)
                if column_type == 'int':
                    order_columns.append(column_name)

            bind_key = 'dimension_%s' % dim.id
            # SQLALCHEMY_BINDS = conf.get('SQLALCHEMY_BINDS', {})
            # for key in SQLALCHEMY_BINDS:
            conf['SQLALCHEMY_BINDS'][bind_key] = dim.sqllchemy_uri
            # if dim.sqllchemy_uri in SQLALCHEMY_BINDS[key]:
            #     bind_key=key
            #     break
            # model 类
            model_class = type(
                "Dimension_Model_%s" % dim.id, (Model, MyappModelBase),
                dict(
                    __tablename__=dim.table_name,
                    __bind_key__=bind_key if bind_key else None,
                    **column_class
                )
            )

            # 页面视图

            url = '/dimension_remote_table_modelview/%s/api/' % dim_id
            print(url)

            def get_primary_key(cols):
                for name in cols:
                    if cols[name].get('primary_key',False):
                        return name
                return ''


            @expose("/upload/", methods=["POST"])
            # @pysnooper.snoop(watch_explode=('attr'))
            def upload(self):
                csv_file = request.files.get('csv_file')  # FileStorage
                dim = db.session.query(Dimension_table).filter_by(id=int(self.dim_id)).first()
                # 文件保存至指定路径
                i_path = csv_file.filename
                if os.path.exists(i_path):
                    os.remove(i_path)
                csv_file.save(i_path)
                # 读取csv，读取header，按行处理
                import csv
                csv_reader = csv.reader(open(i_path, mode='r', encoding='utf-8-sig'))
                header = None
                result = []
                cols = json.loads(dim.columns)
                for line in csv_reader:
                    if not header:
                        header = line
                        # 判断header里面的字段是否在数据库都有
                        for col_name in header:
                            # attr = self.datamodel.obj
                            if not hasattr(self.datamodel.obj, col_name):
                                flash('csv首行header与数据库字段不对应', 'warning')
                                back = {
                                    "status": 1,
                                    "result": [],
                                    "message": "csv首行header与数据库字段不对应"
                                }
                                return self.response(400, **back)
                        continue
                    # 个数不对的去掉
                    if len(line)!=len(header):
                        continue

                    # 全是空值的去掉
                    ll = [l.strip() for l in line if l.strip()]
                    if not ll:
                        continue

                    data = dict(zip(header, line))

                    try:
                        # 把整型做一下转换，因为文件离线全部识别为字符串

                        for key in data:
                            try:
                                data[key]=int(data[key]) if cols.get(key,{}).get('column_type','text')=='int' else str(data[key])
                            except Exception as e:
                                data[key] = None

                        model = self.datamodel.obj(**data)
                        self.pre_add(model)
                        db.session.add(model)
                        self.post_add(model)
                        db.session.commit()
                        result.append('success')
                    # except SQLAlchemyError as ex:
                    #     db.session.rollback()
                    except Exception as e:
                        db.session.rollback()
                        print(e)
                        result.append('fail')

                flash('成功导入%s行，失败导入%s行' % (len([x for x in result if x == 'success']), len([x for x in result if x == 'fail'])), 'success')
                back = {
                    "status": 0,
                    "result": result,
                    "message": "result为上传成功行，共成功%s" % len([x for x in result if x == 'success'])
                }
                return self.response(200, **back)

            @action("muldelete", __("Delete"), __("Delete all Really?"), "fa-trash", single=False)
            # @pysnooper.snoop(watch_explode=('items'))
            def muldelete(self, items):
                if not items:
                    abort(404)
                success = []
                fail = []
                for item in items:
                    try:
                        self.pre_delete(item)
                        db.session.delete(item)
                        success.append(item.to_json())
                    except Exception as e:
                        flash(str(e), "danger")
                        fail.append(item.to_json())
                db.session.commit()
                return json.dumps(
                    {
                        "success": success,
                        "fail": fail
                    }, indent=4, ensure_ascii=False
                )


            view_class = type(
                "Dimension_%s_ModelView_Api"%dim.id, (MyappModelRestApi,),
                dict(
                    datamodel=SQLAInterface(model_class,session=db.session),
                    route_base=url,
                    add_form_extra_fields=add_form_extra_fields,
                    edit_form_extra_fields=add_form_extra_fields,
                    spec_label_columns=spec_label_columns,
                    search_columns=search_columns,
                    order_columns=order_columns,
                    label_title = dim.label,
                    upload=upload,
                    muldelete=muldelete,
                    dim_id=dim_id,
                    import_data=True,
                    download_data=True,
                    cols_width=cols_width,
                    base_order=(get_primary_key(columns), "desc") if get_primary_key(columns) else None
                )
            )
            view_instance = view_class()
            view_instance._init_model_schemas()
            all_dimension["dimension_%s"%dim_id]=view_instance

        return all_dimension["dimension_%s"%dim_id]

    @expose("/<dim_id>/api/_info", methods=["GET"])
    def dim_api_info(self,dim_id, **kwargs):
        view_instance = self.set_model(dim_id)
        return view_instance.api_info(**kwargs)


    @expose("/<dim_id>/api/<int:pk>", methods=["GET"])
    def dim_api_get(self, dim_id,pk, **kwargs):
        view_instance = self.set_model(dim_id)
        return view_instance.api_get(pk,**kwargs)

    @expose("/<dim_id>/api/", methods=["GET"])
    def dim_api_list(self,dim_id, **kwargs):
        view_instance = self.set_model(dim_id)
        return view_instance.api_list(**kwargs)

    @expose("/<dim_id>/api/", methods=["POST"])
    def dim_api_add(self,dim_id):
        view_instance = self.set_model(dim_id)
        return view_instance.api_add()


    @expose("/<dim_id>/api/<pk>", methods=["PUT"])
    # @pysnooper.snoop(watch_explode=('item','data'))
    def dim_api_edit(self, dim_id,pk):
        view_instance = self.set_model(dim_id)
        return view_instance.api_edit(pk)

    @expose("/<dim_id>/api/<pk>", methods=["DELETE"])
    def dim_api_delete(self,dim_id, pk):
        view_instance = self.set_model(dim_id)
        return view_instance.api_delete(pk)

    @expose("/<dim_id>/api/upload/", methods=["POST"])
    # @pysnooper.snoop()
    def dim_api_upload(self,dim_id):
        view_instance = self.set_model(dim_id)
        return view_instance.upload()

    @expose("/<dim_id>/api/download_template/", methods=["GET"])
    # @pysnooper.snoop()
    def dim_api_download_template(self,dim_id):
        view_instance = self.set_model(dim_id)
        return view_instance.download_template()


    @expose("/<dim_id>/api/download/", methods=["GET"])
    # @pysnooper.snoop()
    def dim_api_download(self,dim_id):
        view_instance = self.set_model(dim_id)
        return view_instance.download()

    @expose("/<dim_id>/api/multi_action/<string:name>", methods=["POST"])
    def multi_action(self,dim_id,name):
        view_instance = self.set_model(dim_id)
        return view_instance.multi_action(name)



appbuilder.add_api(Dimension_remote_table_ModelView_Api)






