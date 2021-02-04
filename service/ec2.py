from datetime import datetime, timedelta
from typing import Optional

from boto3.session import Session as BotoSession

from config import webapp_settings
from model import Server
from mysql_dbcon import Connection


class EC2Connector():

    def __init__(self):
        self.boto = BotoSession(
            region_name='ap-northeast-1',
            aws_access_key_id=webapp_settings['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=webapp_settings['AWS_SECRET_KEY'])
        self.ec2 = self.boto.client('ec2')

    def auto_switch_server(self):
        instance_response = self.ec2.describe_instances()
        with Connection() as cn:
            server_list = cn.s.query(Server).filter(Server.is_staging == 0).all()
            db_instance_id_dict = {server.instance_id: server for server in server_list}

            # TODO non-reserved instance
            for r in instance_response['Reservations']:
                for instance in r['Instances']:
                    server: Optional[Server] = db_instance_id_dict.get(instance['InstanceId'])
                    if not server:
                        continue
                    if server.auto_start_at and server.auto_start_at < datetime.now():
                        server.auto_start_at += timedelta(days=1)
                        cn.s.add(server)
                        if instance['State']['Name'] == 'stopped':
                            self.ec2.start_instances(InstanceIds=[server.instance_id])
                    elif server.auto_stop_at and server.auto_stop_at < datetime.now():
                        server.auto_stop_at += timedelta(days=1)
                        cn.s.add(server)
                        if instance['State']['Name'] == 'running':
                            self.ec2.stop_instances(InstanceIds=[server.instance_id])
            cn.s.commit()
