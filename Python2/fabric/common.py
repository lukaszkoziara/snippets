import boto.ec2
from fabric.api import local, sudo, run
from fabric.exceptions import NetworkError


AWS_ID = 'someid'
AWS_KEY = 'somekey'
AWS_REGION = 'eu-west-1'


server_names = {
    'test1': {
        'deploy_name': 'Test1',  # for slack printing info
        'app_name': 'some-app',  # point app folder and virtualenv name
        'aws_names': ['Test1-Prod'],  # for extracting aws resources by tag/names
        'autoscaling': True  # whether to update LC and ASG
    },
    'test2': {
        'deploy_name': 'Test2',
        'app_name': 'some-app',
        'aws_names': ['Test2-Prod'],
        'autoscaling': True
    },
    'all-test': {
        'deploy_name': 'All Tests',
        'app_name': 'some-app',
        'aws_names': ['Test1-Prod', 'Test2-Prod'],
        'autoscaling': True
    }
}


def set_ec2_conn():
    return boto.ec2.connect_to_region(AWS_REGION, aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_KEY)


def get_setting(key, setting_key):
    return server_names[key][setting_key]


def network_error_catcher(func):
    def func_wrapper(device):
        try:
            func(device)
        except NetworkError:
            print "Device: {} is probably switched off".format(device)
    return func_wrapper


def call_banner():
    sudo("cat /etc/update-motd.d/30-banner")


@network_error_catcher
def replace_ascii_banner(device):
    sudo('cp -f /home/ec2-user/custom-ascii-banner /etc/update-motd.d/30-banner')
    sudo('/usr/sbin/update-motd')


@network_error_catcher
def ram_usage(device, top=5):
    """shows  percentage ram usage with top 5 processes"""
    call_banner()
    sudo("free -t | grep 'buffers/cache' | awk '{print \"RAM IN USE (%):          \" $3/($3+$4) * 100.0}'")
    sudo("echo 'TOP 5 PROCESSES:'")
    sudo("ps aux | awk '{print $2, $4, $11}' | sort -k2rn | head -n \%s" % top)


@network_error_catcher
def disk_usage(device):
    """shows  percentage ram usage with top 5 processes"""
    call_banner()
    run("df -a | grep \"/$\" | awk '{printf \"Disk usage is: %.2f%\\n\", $3/($4+$3)*100}'")


@network_error_catcher
def yum_update(device):
    call_banner()
    sudo('yum update -y')


@network_error_catcher
def clear_yum_cache(device):
    call_banner()
    sudo('yum clean all')


def slack(message):
    local('curl -X POST --data-urlencode \'payload={"text": "' + message + '", "channel": "#general",' +
          '"username": "fabric-bot", "icon_url": "http://www.fabfile.org/_static/logo.png"}\' ' +
          'https://hooks.slack.com/services/111/222/333')
