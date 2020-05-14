import base64
from datetime import datetime
import json
import subprocess
import traceback
import urllib.request

from boto3.session import Session as BotoSession
import jwt

from config import webapp_settings
from model import Server, PullRequest, GitHubUser
from mysql_dbcon import Connection


class GitHubConnector():

    def __init__(self):
        n = int(datetime.now().timestamp())
        payload = {
            'iat': n,
            'exp': n + (10 * 60),
            'iss': int(webapp_settings['github_app_id'])
        }
        try:
            with open(webapp_settings['github_private_key']) as f:
                self.key = ''.join(f.readlines()).encode()
            self.jwt_token = jwt.encode(payload, self.key, algorithm='RS256')
            req = urllib.request.Request(
                f'https://api.github.com/app/installations/{webapp_settings["github_app_installation_id"]}'
                f'/access_tokens',
                headers={
                    'Authorization': f'Bearer {self.jwt_token.decode()}',
                    'Accept': 'application/vnd.github.machine-man-preview+json',
                },
                method='POST'
            )
            with urllib.request.urlopen(req) as res:
                app_result = json.loads(res.read())
            print(app_result)
            self.token = app_result['token']
            print('got github token...')
        except Exception as ex:
            print(ex)
            print(traceback.format_exc())
            if hasattr(ex, 'fp') and hasattr(ex.fp, 'read') and callable(ex.fp.read):
                print(ex.fp.read())
            self.token = None
            print('no github token...')

    def check_and_update_pull_request(self):
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
                    PullRequest.server_id == Server.id, PullRequest.state == 'open').exists()
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
                            print(ex)
                            print(traceback.format_exc())
                            raise ex
                        if self.token:
                            self.post_and_set_check_run(new_db_pull_request, pull_request, server)
                    cn.s.add(new_db_pull_request)
                else:
                    # update (if status was changed)
                    db_pull_request = db_number_dict[pull_request['number']]
                    if db_pull_request.sha != pull_request['sha']:
                        db_pull_request.sha = pull_request['sha']
                        db_pull_request.is_launched = 0
                        if self.token:
                            server = db_pull_request.server
                            self.post_and_set_check_run(db_pull_request, pull_request, server)
                            cn.s.add(server)

                    if db_pull_request.state != pull_request['state']:
                        if db_pull_request.state == 'open':
                            # close
                            ec2.stop_instances(InstanceIds=[db_pull_request.server.instance_id])
                        db_pull_request.state = pull_request['state']
                    cn.s.add(db_pull_request)
            cn.s.commit()

            if self.token:
                server_list = cn.s.query(Server, PullRequest).join(
                    PullRequest, Server.id == PullRequest.server_id).filter(
                    PullRequest.state == 'open'
                ).all()

                for server, pr in server_list:
                    try:
                        req = urllib.request.Request(server.check_url)
                        with urllib.request.urlopen(req) as res:
                            print(res.read())
                        # when come this line, server returns 20X/30X
                        self.patch_check_run(pr.check_run_id)
                        pr.check_run_id = None
                        cn.s.add(pr)
                        cn.s.commit()
                    except Exception as ex:
                        print(ex)
                        print(traceback.format_exc())
                        if hasattr(ex, 'fp') and hasattr(ex.fp, 'read') and callable(ex.fp.read):
                            print(ex.fp.read())

        return github_pull_request_list

    def post_and_set_check_run(self, db_pull_request, pull_request, server):
        try:
            check_run_result = self.post_check_run(pull_request['sha'], server.check_url)
            db_pull_request.check_run_id = check_run_result['id']
        except Exception as ex:
            print(ex)
            print(traceback.format_exc())
            if hasattr(ex, 'fp') and hasattr(ex.fp, 'read') and callable(ex.fp.read):
                print(ex.fp.read())
            raise ex

    def post_check_run(self, head_sha, details_url):
        payload = {
            'name': 'pullre-kun',
            'head_sha': head_sha,
            'details_url': details_url,
            'started_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
        req = urllib.request.Request(
            f'https://api.github.com/repos/{webapp_settings["owner"]}/{webapp_settings["repo"]}/check-runs',
            headers={
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.antiope-preview+json',
            },
            data=json.dumps(payload).encode(),
            method='POST'
        )
        with urllib.request.urlopen(req) as res:
            check_run_result = json.loads(res.read())
        return check_run_result

    def patch_check_run(self, check_run_id):
        payload = {
            'completed_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'status': 'completed',
            'conclusion': 'success',
        }
        req = urllib.request.Request(
            f'https://api.github.com/repos/{webapp_settings["owner"]}/{webapp_settings["repo"]}'
            f'/check-runs/{check_run_id}',
            headers={
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.antiope-preview+json',
            },
            data=json.dumps(payload).encode(),
            method='PATCH'
        )
        with urllib.request.urlopen(req) as res:
            check_run_result = json.loads(res.read())
        return check_run_result
