from flask import render_template,redirect
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi
from flask_appbuilder import ModelView,AppBuilder,expose,BaseView,has_access
from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
# 将model添加成视图，并控制在前端的显示
from myapp.models.model_team import Project,Project_User
from myapp.views.view_team import Project_User_ModelView,Project_Filter
from flask_appbuilder.actions import action
from wtforms import BooleanField, IntegerField, SelectField, StringField,FloatField,DateField,DateTimeField,SelectMultipleField,FormField,FieldList
from flask_appbuilder.models.sqla.filters import FilterEqualFunction, FilterStartsWith,FilterEqual,FilterNotEqual
from wtforms.validators import EqualTo,Length
from flask_babel import lazy_gettext,gettext
from flask_appbuilder.security.decorators import has_access
from myapp.utils import core
from myapp import app, appbuilder,db
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask_appbuilder.fieldwidgets import Select2Widget
from myapp.exceptions import MyappException
from myapp import conf, db, get_feature_flags, security_manager,event_logger
from myapp.forms import MyBS3TextFieldWidget
from flask import (
    abort,
    flash,
    g,
    Markup,
    redirect,
    render_template,
    request,
    Response,
    url_for,
)
from .base import (
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
from .baseApi import (
    MyappModelRestApi
)
import pysnooper,datetime,time,json
from flask_appbuilder import CompactCRUDMixin, expose



# @pysnooper.snoop()
class Project_ModelView_Base():
    label_title='项目组'
    datamodel = SQLAInterface(Project)
    base_permissions = ['can_add', 'can_edit', 'can_delete', 'can_list', 'can_show']  # 默认为这些
    base_order = ('id', 'desc')
    list_columns = ['name','user','type']
    related_views = [Project_User_ModelView,]
    add_columns = ['type','name','describe','expand']
    edit_columns = add_columns

    # edit_form_extra_fields={
    #     'type':StringField(
    #         _(datamodel.obj.lab('type')),
    #         description="项目分组",
    #         widget=MyBS3TextFieldWidget(value=project_type, readonly=1),
    #         default=project_type,
    #     )
    # }
    #
    # add_form_extra_fields = edit_form_extra_fields

    # @pysnooper.snoop(watch_explode=('aa',))
    def pre_add_get(self):
        self.edit_form_extra_fields['type'] = StringField(
            _(self.datamodel.obj.lab('type')),
            description="项目分组",
            widget=MyBS3TextFieldWidget(value=self.project_type,readonly=1),
            default=self.project_type,
        )

        self.add_form_extra_fields = self.edit_form_extra_fields


    # 打开编辑前，校验权限
    def pre_update_get(self, item):
        self.pre_add_get()
        user_roles = [role.name.lower() for role in list(get_user_roles())]
        if "admin" in user_roles:
            return
        if not g.user.username in item.get_creators():
            flash('just creator can add/edit user','warning')
            raise MyappException('just creator can add/edit user')


    def pre_update(self, item):
        if item.expand:
            core.validate_json(item.expand)
            item.expand = json.dumps(json.loads(item.expand),indent=4,ensure_ascii=False)
        user_roles = [role.name.lower() for role in list(get_user_roles())]
        if "admin" in user_roles:
            return
        if not g.user.username in item.get_creators():
            raise MyappException('just creator can add/edit')

        # 检测是否具有编辑权限，只有creator和admin可以编辑



    # @pysnooper.snoop()
    def project_init(self,item):
        try:
            if item.type == 'embedding':
                # 查看创建七彩石的分组和添加配置
                from rainbow_admin import RainbowAdmin
                admin = RainbowAdmin(
                    app_id="60dfd88e-3d06-461a-b5ff-6e87c9c89faf",
                    user_id="3a7f2dacdfae40d480e121b2a59a8b37",
                    secret_key="2ea307b84a20ac71408eb7d5283aab171dab",
                    # env='test'
                )
                group = admin["%s" % item.name]
                if not group:
                    admin.create_group("%s" % item.name)
                    group = admin["%s" % item.name]
                    # flash('七彩石分组%s创建成功' % item.name, 'success')

                # 添加ef分组信息，通过七彩石global分组信息来实现
                group = admin["global"]
                ef_monitor_group = group['groups']
                ef_monitor_group = ef_monitor_group.split(',')
                ef_monitor_group = [ef_group.strip() for ef_group in ef_monitor_group if ef_group.strip()] + [item.name]
                ef_monitor_group = list(set(ef_monitor_group))
                ef_monitor_group = ','.join(ef_monitor_group)
                group['groups'] = ef_monitor_group

                flash('添加七彩石配置成功','success')


        except Exception as e:
            flash('添加七彩石配置失败，请重新保存：%s'%str(e),'warning')

    # 添加创始人
    def post_add(self, item):
        creator = Project_User(role='creator',user=g.user,project=item)
        db.session.add(creator)
        db.session.commit()
        self.project_init(item)



    # 自动更新分组
    def post_update(self,item):
        self.project_init(item)

    # @pysnooper.snoop()
    def post_list(self,items):
        return core.sort_expand_index(items,db.session)



class Project_ModelView_embedding(Project_ModelView_Base,MyappModelView):
    project_type = 'embedding'
    base_filters = [["id", Project_Filter, project_type]]  # 设置权限过滤器
    datamodel = SQLAInterface(Project)

    edit_form_extra_fields={
        'type':StringField(
            _(datamodel.obj.lab('type')),
            description="项目分组",
            widget=MyBS3TextFieldWidget(value=project_type, readonly=1),
            default=project_type,
        )
    }

    add_form_extra_fields = edit_form_extra_fields



appbuilder.add_view(Project_ModelView_embedding,"Embedding分组",icon = 'fa-address-book-o',category = '项目组',category_icon = 'fa-users')






