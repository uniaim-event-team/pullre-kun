from flask import Blueprint, render_template, request, redirect
from form.master import MasterForm, MasterSearchForm, table_label_dict

from mysql_dbcon import Connection
from controller.common import url_for_ep

app = Blueprint(__name__, "master")


@app.route('/master')
@need_basic_auth
def master_top():
    return render_template('master/top.html', table_names=[table_name for table_name in table_label_dict.keys()])


@app.route('/master/<table_name>')
@app.route('/master/<table_name>/list')
@need_basic_auth
def master_list(table_name):
    if request.method == 'GET':
        with Connection() as cn:
            form = MasterSearchForm.generate(table_label_dict[table_name].model, cn)
            count = int(request.values.get('count', 100))
            page = int(request.values.get('page', 0))
            list_query = cn.s.query(table_label_dict[table_name].model)
            # TODO filter data
            list_data = [r.__dict__ for r in list_query.limit(count).offset(count * page).all()]
            columns = [column.name for column in table_label_dict[table_name].model.__table__.columns]
        return render_template(
            'master/list.html', form=form, list_data=list_data, columns=columns, table_name=table_name)


@app.route('/master/<table_name>/create', methods=['GET', 'POST'])
@need_basic_auth
def master_create(table_name):
    if request.method == 'GET':
        with Connection() as cn:
            form = MasterForm.generate(table_label_dict[table_name].model, cn)
        return render_template('master/update.html', form=form, button='create', table_name=table_name)
    if request.method == 'POST':
        with Connection() as cn:
            form = MasterForm.generate(table_label_dict[table_name].model, cn)
            if not form.validate_on_submit():
                return render_template('master/update.html', form=form, button='create', table_name=table_name)
            cn.upsert_from_form(table_label_dict[table_name].model, form)
        return redirect(url_for_ep('controller.master.master_create', table_name=table_name))


@app.route('/master/<table_name>/<int:id_>/update', methods=['GET', 'POST'])
@need_basic_auth
def master_update(table_name, id_):
    if request.method == 'GET':
        with Connection() as cn:
            model = table_label_dict[table_name].model
            obj = cn.s.query(model).filter(model.id == id_).one()
            form = MasterForm.generate(model, cn, obj=obj)
        return render_template('master/update.html', form=form, button='update', table_name=table_name)
    if request.method == 'POST':
        with Connection() as cn:
            model = table_label_dict[table_name].model
            obj = cn.s.query(model).filter(model.id == id_).one()
            form = MasterForm.generate(model, cn, obj=obj)
            if not form.validate_on_submit():
                return render_template('master/update.html', form=form, button='update', table_name=table_name)
            cn.upsert_from_form(table_label_dict[table_name].model, form)
        return render_template('master/update.html', form=form, button='update', table_name=table_name)


@app.route('/master/<table_name>/<int:id_>')
@need_basic_auth
def master_show(table_name, id_):
    if request.method == 'GET':
        with Connection() as cn:
            model = table_label_dict[table_name].model
            obj = cn.s.query(model).filter(model.id == id_).one()
            form = MasterForm.generate(model, cn, obj=obj, freeze=True)
        return render_template('master/update.html', form=form, button='', table_name=table_name)


@app.route('/master/<table_name>/<int:id_>/delete', methods=['GET', 'POST'])
@need_basic_auth
def master_delete(table_name, id_):
    if request.method == 'GET':
        with Connection() as cn:
            model = table_label_dict[table_name].model
            obj = cn.s.query(model).filter(model.id == id_).one()
            form = MasterForm.generate(model, cn, obj=obj, freeze=True)
        return render_template('master/update.html', form=form, button='delete', table_name=table_name)
    if request.method == 'POST':
        with Connection() as cn:
            model = table_label_dict[table_name].model
            cn.s.query(model).filter(model.id == id_).delete(synchronize_session=False)
            cn.s.commit()
        return redirect(url_for_ep('controller.master.master_list', table_name=table_name))
