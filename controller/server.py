import json
from typing import Optional

from boto3.session import Session as BotoSession
from flask import Blueprint, render_template, request

from basic import need_basic_auth
from config import webapp_settings
from formatter import safe_strftime
from model import Server, HideServer
from mysql_dbcon import Connection
from service.pull import GitHubConnector

app = Blueprint(__name__, "server")


@app.route('/')
def route():
    return render_template('top.html')


@app.route('/server/list')
@need_basic_auth
def server_list():
    boto = BotoSession(
        region_name='ap-northeast-1',
        aws_access_key_id=webapp_settings['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=webapp_settings['AWS_SECRET_KEY'])
    ec2 = boto.client('ec2')
    instance_response = ec2.describe_instances()

    with Connection() as cn:
        server_list = cn.s.query(Server).all()
        db_instance_id_dict = {server.instance_id: server for server in server_list}
        hide_server_name_set = {hide_server.name for hide_server in cn.s.query(HideServer).all()}

    instance_list = []
    # TODO non-reserved instance
    for r in instance_response['Reservations']:
        for instance in r['Instances']:
            name_tag = [tag for tag in instance['Tags'] if tag['Key'] == 'Name']
            name = name_tag[0]['Value'] if name_tag else ''
            if name in hide_server_name_set:
                continue
            server: Optional[Server] = db_instance_id_dict.get(instance['InstanceId'])
            instance_list.append({
                'InstanceId': instance['InstanceId'],
                'State': instance['State']['Name'],
                'Name': name,
                'PrivateIpAddress': instance['NetworkInterfaces'][0]['PrivateIpAddress']
                if instance['NetworkInterfaces'] else '',
                'Registered': instance['InstanceId'] in db_instance_id_dict,
                'Staging': server and server.is_staging,
                'AutoStartAt': safe_strftime(server and server.auto_start_at),
                'AutoStopAt': safe_strftime(server and server.auto_stop_at),
                'Id': server and server.id,
            })
    instance_list.sort(key=lambda x: x['Name'] + '____' + x['InstanceId'])
    return render_template('server/list.html', instance_list=instance_list)


@app.route('/server/register', methods=['POST'])
@need_basic_auth
def server_register():
    with Connection() as cn:
        cn.s.add(Server(
            instance_id=request.values['InstanceId'],
            name=request.values['Name'],
            private_ip=request.values['PrivateIpAddress'],
        ))
        cn.s.commit()
    return 'add server to database.'


@app.route('/server/start', methods=['POST'])
@need_basic_auth
def server_start():
    boto = BotoSession(
        region_name='ap-northeast-1',
        aws_access_key_id=webapp_settings['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=webapp_settings['AWS_SECRET_KEY'])
    ec2 = boto.client('ec2')
    start_response = ec2.start_instances(InstanceIds=[request.values.get('InstanceId')])
    return start_response


@app.route('/server/stop', methods=['POST'])
@need_basic_auth
def server_stop():
    boto = BotoSession(
        region_name='ap-northeast-1',
        aws_access_key_id=webapp_settings['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=webapp_settings['AWS_SECRET_KEY'])
    ec2 = boto.client('ec2')
    stop_response = ec2.stop_instances(InstanceIds=[request.values.get('InstanceId')])
    return stop_response


@app.route('/pull/list')
@need_basic_auth
def pull_list():
    # for manual update
    gc = GitHubConnector()
    return json.dumps(gc.check_and_update_pull_request())


@app.route('/webhook/push', methods=['POST'])
def webhook_push():
    gc = GitHubConnector()
    return json.dumps(gc.check_and_update_pull_request())
