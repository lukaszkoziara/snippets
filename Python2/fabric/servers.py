from fabric.api import execute

from common import replace_ascii_banner, ram_usage, disk_usage, get_setting, set_ec2_conn, yum_update, clear_yum_cache, \
    slack
from updaters import EC2Resource


ec2_conn = set_ec2_conn()


class BaseServer(object):
    SLACK_PREFIX = 'SERVER'

    aws_names = []
    key = ''

    def __init__(self):
        self.aws_names = get_setting(self.key, 'aws_names')

        ec2_resource = EC2Resource(ec2_conn, self.aws_names)
        self.private_ips, self.ids = ec2_resource.get_private_ips()

    def call_update(self):
        for device in self.private_ips:
            execute(yum_update, device, hosts=device)

    def call_clear_yum_cache(self):
        for device in self.private_ips:
            execute(clear_yum_cache, device, hosts=device)

    def call_replace_ascii_banner(self):
        for device in self.private_ips:
            execute(replace_ascii_banner, device, hosts=device)

    def call_ram_usage(self):
        for device in self.private_ips:
            execute(ram_usage, device, hosts=device)

    def update(self):
        slack('%s: Running %s server(s) update...' % (self.SLACK_PREFIX, self.key))
        self.call_update()
        self.call_replace_ascii_banner()
        slack('... All done! :humalon:')

    def clear_yum_cache(self):
        slack('%s: Running %s server(s) clear yum cache...' % (self.SLACK_PREFIX, self.key))
        self.call_clear_yum_cache()
        slack('... All done! :humalon:')

    def ram_usage(self):
        self.call_ram_usage()

    def disk_usage(self):
        for device in self.private_ips:
            execute(disk_usage, device, hosts=device)