from collections import namedtuple
import re

from flask_wtf import FlaskForm
from wtforms.fields import StringField, SelectField, TextAreaField, IntegerField, DateTimeField
from wtforms.validators import input_required

import model


default_readonly_fields = ('id', 'created_at', 'updated_at')
default_label_columns = ('name', 'title', 'label', 'description', 'id')
table_label_dict = {}
TableLabelTuple = namedtuple('TableLabelTuple', ('model', 'label'))
for key, value in model.__dict__.items():
    if str(value).find("model.") > -1:
        for column_name in default_label_columns:
            if hasattr(value, column_name):
                table_label_dict[value.__tablename__] = TableLabelTuple(
                    value, getattr(value, column_name).name)
                break


class MasterForm(FlaskForm):
    """
    Generate very generalized update form
    """
    @staticmethod
    def generate(model_class, cn, readonly_fields=default_readonly_fields, freeze=False, obj=None):
        class GeneratedForm(MasterForm):
            pass
        if model_class:
            for column in model_class.__table__.columns:
                _nullable = column.nullable
                _type = str(column.type)
                validators = []
                if not _nullable and column.name not in readonly_fields:
                    validators += [input_required()]
                render_kw = {}
                if freeze or column.name in readonly_fields:
                    render_kw['disabled'] = 'disabled'
                if column.foreign_keys:
                    # TODO multiple foreign keys
                    # TODO one key has multiple columns
                    # TODO when foreign key is readonly, validate always fails (bug)
                    parent_table_name = re.sub(".+'", '', str(list(column.foreign_keys)[0]).split('.')[0])
                    _cls, _label = table_label_dict[parent_table_name]
                    choices = [('', '(choose)')] + [
                        (str(a), b) for a, b in cn.s.query(_cls.id, getattr(_cls, _label)).limit(1000).all()]
                    setattr(GeneratedForm, column.name, SelectField(
                        column.name, choices=choices, validators=validators, render_kw=render_kw))
                elif _type == 'BIGINT' or _type.find('INT') > -1:
                    setattr(GeneratedForm, column.name, IntegerField(
                        column.name, validators=validators, render_kw=render_kw))
                elif _type.find('VARCHAR') > -1:
                    setattr(GeneratedForm, column.name, StringField(
                        column.name, validators=validators, render_kw=render_kw))
                elif _type.find('TEXT') > -1:
                    setattr(GeneratedForm, column.name, TextAreaField(
                        column.name, validators=validators, render_kw=render_kw))
                elif _type == 'DATETIME':
                    setattr(GeneratedForm, column.name, DateTimeField(
                        column.name, validators=validators, render_kw=render_kw))
        return GeneratedForm(obj=obj)


class MasterSearchForm(FlaskForm):
    """
    Generate very generalized search form
    """
    @staticmethod
    def generate(model_class, cn, ignore_fields=(), obj=None):
        class GeneratedForm(MasterSearchForm):
            pass
        if model_class:
            # TODO set form controls...
            print(ignore_fields)
            print(cn)
        return GeneratedForm(obj=obj)
