import socket
import subprocess

from model import PullRequest, Server
from mysql_dbcon import Connection, webapp_settings


if __name__ == '__main__':
    host = socket.gethostname()
    ip = socket.gethostbyname(host)

    need_launch = False
    with Connection() as cn:
        pull_requests = cn.s.query(PullRequest).join(PullRequest.server).filter(
            Server.private_ip == ip, PullRequest.state == 'open', PullRequest.is_launched == 0).all()
        if len(pull_requests) > 0:
            print('set unprocessed pull request...')
            pr = pull_requests[0]
            res = subprocess.check_output(
                f'cd {webapp_settings["base_dir"]} | git fetch | git checkout {pr.sha}', shell=True)
            pr.is_launched = 1
            cn.s.commit()
            need_launch = True
        if len(pull_requests) > 1:
            print('delete pull requests, because there are too many pull requests...')
            cn.s.query(PullRequest).filter(PullRequest.id.in_([p.id for p in pull_requests[1:]])).delete(
                synchronize_session=False)
            cn.s.commit()

    if need_launch:
        print('killing process...')
        subprocess.check_output(
            "ps -ef | grep -v grep| grep " + webapp_settings['exec_command_grep'] +
            """ | awk '{print "sudo kill -9", $2}' | bash""", shell=True)
        print('launch...')
        res = subprocess.check_output(
            f'{webapp_settings["exec_command"]}', shell=True)
