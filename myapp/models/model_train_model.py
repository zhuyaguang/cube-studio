from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey,Float
from sqlalchemy.orm import relationship
import datetime,time,json
from sqlalchemy import (
    Boolean,
    Column,
    create_engine,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    Enum,
)
from myapp.utils.py.py_k8s import K8s
from myapp.models.helpers import AuditMixinNullable, ImportMixin
from flask import escape, g, Markup, request
from .model_team import Project
from .model_job import Pipeline
from myapp import app,db
from myapp.models.base import MyappModelBase
from myapp.models.helpers import ImportMixin
# 添加自定义model
from sqlalchemy import Column, Integer, String, ForeignKey ,Date,DateTime
from flask_appbuilder.models.decorators import renders
from flask import Markup
import datetime
metadata = Model.metadata
conf = app.config


# 定义训练 model
class Training_Model(Model,AuditMixinNullable,MyappModelBase):
    __tablename__ = 'model'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    version = Column(String(100))
    describe = Column(Text)
    path = Column(String(200))
    download_url = Column(String(200))
    project_id = Column(Integer, ForeignKey('project.id'))  # 定义外键
    project = relationship(
        Project, foreign_keys=[project_id]
    )
    pipeline_id = Column(Integer, ForeignKey('pipeline.id'))  # 定义外键
    pipeline = relationship(
        Pipeline, foreign_keys=[pipeline_id]
    )
    run_id = Column(String(100),nullable=False)   # 可能同一个pipeline产生多个模型
    run_time = Column(String(100))
    framework = Column(String(100))
    metrics = Column(Text,default='{}')
    md5 = Column(String(200),default='')
    status = Column(Enum('offline','test','online','delete'),nullable=False,default='offline')
    api_type = Column(String(100))
    label_columns_add = {
        "path": "模型文件",
        "framework":"算法框架",
    }
    label_columns=MyappModelBase.label_columns.copy()
    label_columns.update(label_columns_add)

    def __repr__(self):
        return self.name

    # 获取模型的部署情况
    def get_deploy(self):
        return db.session().query(Training_Model_Deploy).filter_by(train_model_id=self.id).all()

    @property
    def pipeline_url(self):
        if self.pipeline:
            return Markup(f'<a target=_blank href="/pipeline_modelview/list/?_flt_2_name={self.pipeline.name}">{self.pipeline.describe}</a>')
        else:
            return Markup(f'未知')

    @property
    def project_url(self):
        if self.project:
            return Markup(f'{self.project.name}({self.project.describe})')
        elif self.pipeline and self.pipeline.project:
            return Markup(f'{self.pipeline.project.name}({self.pipeline.project.describe})')
        else:
            return Markup(f'未知')

    @property
    def check_test_service(self):
        return Markup(f'<a href="/training_model_modelview/deploy/check_test/{self.id}">检测测试服务</a>')

    @property
    def test_deploy(self):
        return Markup(f'<a href="/training_model_modelview/deploy/test/{self.id}">部署测试环境</a>')

    @property
    def prod_deploy(self):
        return Markup(f'<a href="/training_model_modelview/deploy/prod/{self.id}">部署生产</a>')


# 定义模型部署 model
class Training_Model_Deploy(Model,AuditMixinNullable,MyappModelBase):
    __tablename__ = 'deploy'
    id = Column(Integer, primary_key=True)
    train_model_id = Column(Integer, ForeignKey('model.id'))  # 定义外键
    train_model = relationship(
        Training_Model, foreign_keys=[train_model_id]
    )
    ip = Column(String(100), nullable=False)
    deploy_time = Column(String(100), nullable=False,default=datetime.datetime.now)
    status = Column(Enum('offline', 'online', 'delete'), nullable=False, default='offline')

    @property
    def model_name(self):
        return Markup(
            f'<a target=_blank href="/training_model_modelview/list/?_flt_3_name={self.train_model.name}">{self.train_model.name}</a>')

    @property
    def pipeline(self):
        return Markup(f'<a target=_blank href="/pipeline_modelview/list/?_flt_2_name={self.train_model.pipeline.name}">{self.train_model.pipeline.describe}</a>')

    @property
    def run_id(self):
        return self.train_model.run_id


