from service.ec2 import EC2Connector


if __name__ == '__main__':
    ec = EC2Connector()
    ec.auto_switch_server()
