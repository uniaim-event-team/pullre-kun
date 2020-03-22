import base64
import json
import subprocess
import urllib.request

from boto3.session import Session as BotoSession

from config import webapp_settings
from model import Server, PullRequest, GitHubUser
from mysql_dbcon import Connection


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
                    github_user = cn.s.query(GitHubUser).filter(
                        GitHubUser.login == pull_request['login']).first()
                    if not github_user:
                        github_user = cn.s.query(GitHubUser).first()
                    db_schema = github_user.db_schema
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
                            f'{webapp_settings["base_dir"]}/setup_db.sh {db_schema} {server.db_schema}'
                            f' {webapp_settings["mysql_user"]} {webapp_settings["mysql_pw"]}'
                            f' {webapp_settings["mysql_host"]} {webapp_settings["mysql_port"]}', shell=True)
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
