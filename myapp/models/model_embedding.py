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
class Embedding(Model,AuditMixinNullable,MyappModelBase):
    __tablename__ = 'embedding'
    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), nullable=False)
    version = Column(String(100))
    describe = Column(Text)
    model_path = Column(String(200))
    embedding_file_path = Column(String(200))
    is_fallback = Column(Boolean, default=False)
    project_id = Column(Integer, ForeignKey('project.id'))  # 定义外键
    project = relationship(
        Project, foreign_keys=[project_id]
    )
    pipeline_id = Column(Integer, ForeignKey('pipeline.id'))  # 定义外键
    pipeline = relationship(
        Pipeline, foreign_keys=[pipeline_id]
    )
    run_id = Column(String(100),nullable=False,unique=True)
    create_time = Column(String(100))
    metrics = Column(Text,default='{}')
    status = Column(Enum('offline','online'),nullable=False,default='offline')

    def __repr__(self):
        return self.model_name

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
    def check_service(self):
        return Markup(f'<a href="/embedding_modelview/deploy/check_service/{self.id}">检查服务状态</a>')

    @property
    def prod_deploy(self):
        return Markup(f'<a href="/embedding_modelview/deploy/prod/{self.id}">部署生产</a>')


