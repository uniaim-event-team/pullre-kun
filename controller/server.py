import base64
import json
import subprocess
import urllib.request

from boto3.session import Session as BotoSession
from flask import Blueprint, render_template, request

from basic import need_basic_auth
from config import webapp_settings
from model import Server, PullRequest, GitHubUser
from mysql_dbcon import Connection

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
        db_instance_id_list = [server.instance_id for server in cn.s.query(Server).all()]

    instance_list = []
    # TODO non-reserved instance
    for r in instance_response['Reservations']:
        for instance in r['Instances']:
            name_tag = [tag for tag in instance['Tags'] if tag['Key'] == 'Name']
            instance_list.append({
                'InstanceId': instance['InstanceId'],
                'State': instance['State']['Name'],
                'Name': name_tag[0]['Value'] if name_tag else '',
                'PrivateIpAddress': instance['NetworkInterfaces'][0]['PrivateIpAddress']
                if instance['NetworkInterfaces'] else '',
                'Registered': instance['InstanceId'] in db_instance_id_list,
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
    return json.dumps(check_and_update_pull_request())


def check_and_update_pull_request():
    basic_digest = base64.b64encode(
        (webapp_settings["owner"] + ':' + webapp_settings["token"]).encode()).decode()
    # TODO  too many pull_requests
    req = urllib.request.Request(
        f'https://api.github.com/repos/{webapp_settings["owner"]}/{webapp_settings["repo"]}/pulls?state=all',
        headers={'Authorization': f'Basic {basic_digest}'}
    )
    with urllib.request.urlopen(req) as res:
        pull_request_list = json.loads(res.read())

    github_pull_request_list = [{
        'number': p['number'],
        'state': p['state'],
        'sha': p['head']['sha'],
        'title': p['title'],
        'ref': p['head']['ref'],
        'login': p['user']['login'],
    } for p in pull_request_list]

    boto = BotoSession(
        region_name='ap-northeast-1',
        aws_access_key_id=webapp_settings['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=webapp_settings['AWS_SECRET_KEY'])
    ec2 = boto.client('ec2')

    with Connection() as cn:
        db_pull_request_list = cn.s.query(PullRequest).filter(
            PullRequest.number.in_([p['number'] for p in github_pull_request_list])).all()
        # insert pull requests
        db_number_dict = {p.number: p for p in db_pull_request_list}
        stopped_server_list = cn.s.query(Server).filter(
            ~cn.s.query(PullRequest).filter(
                PullRequest.server_id == Server.id, PullRequest.state != 'open').exists()
        ).all()
        for pull_request in github_pull_request_list:
            if pull_request['number'] not in db_number_dict.keys():
                if not stopped_server_list:
                    continue
                db_schema = ''
                if not db_schema:
                    db_schema = cn.s.query(GitHubUser).filter(
                        GitHubUser.login == pull_request['login']).one().db_schema
                # insert
                new_db_pull_request = PullRequest(
                    number=pull_request['number'],
                    state=pull_request['state'],
                    sha=pull_request['sha'],
                    title=pull_request['title'],
                    ref=pull_request['ref'],
                    is_launched=0,
                    db_schema=db_schema,
                )
                if new_db_pull_request.state == 'open':
                    server = stopped_server_list.pop()
                    new_db_pull_request.server_id = server.id
                    ec2.start_instances(InstanceIds=[server.instance_id])
                    # drop / create and copy database
                    try:
                        subprocess.check_output(
                            f'{webapp_settings["base_dir"]}/setup_db.sh {db_schema} {server.db_schema}', shell=True)
                    except Exception as ex:
                        print(ex.__dict__)
                        raise ex
                cn.s.add(new_db_pull_request)
            else:
                # update (if status was changed)
                db_pull_request = db_number_dict[pull_request['number']]
                if db_pull_request.sha != pull_request['sha']:
                    db_pull_request.sha = pull_request['sha']
                    db_pull_request.is_launched = 0
                if db_pull_request.state != pull_request['state']:
                    if db_pull_request.state == 'open':
                        # close
                        ec2.stop_instances(InstanceIds=[db_pull_request.server.instance_id])
                    db_pull_request.state = pull_request['state']
                cn.s.add(db_pull_request)
        cn.s.commit()

    return github_pull_request_list
