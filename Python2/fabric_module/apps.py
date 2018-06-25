import random

from fabric.api import cd, execute, prefix, run, sudo

from common import get_setting, slack, has_autoscaling_conf, set_autoscale_conn
from servers import ec2_conn
from updaters import EC2Resource, AMIUpdater, AMINameExists, TagUpdater, ASGUpdater

BASE_PATH = '/home/ec2-user/'

autoscale_conn = set_autoscale_conn()


class InitBase(object):
    key = None
    deploy_name = None
    app_name = None

    def __init__(self):
        super(InitBase, self).__init__()
        self.aws_names = get_setting(self.key, 'aws_names')
        self.deploy_name = get_setting(self.key, 'deploy_name') or self.deploy_name
        self.app_name = get_setting(self.key, 'app_name') or self.app_name

        ec2_resource = EC2Resource(ec2_conn, self.aws_names)
        self.private_ips, self.ids = ec2_resource.get_private_ips()


class DeployApp(InitBase):
    SUPERVISED_APPS = []
    SLACK_PREFIX = 'PROD'

    key = ''
    name_tags = []
    aws_names = []
    deploy_name = ''
    app_name = ''

    def _activate_virtualenv(self):
        return prefix('source {}.virtualenvs/{}/bin/activate'.format(BASE_PATH, self.app_name))

    def deploy(self):
        slack('%s: Running %s deploy...' % (self.SLACK_PREFIX, self.deploy_name))
        self.call_supervisor('stop')
        execute(self.deploy_code, hosts=self.private_ips)
        self.call_supervisor('start')
        slack('... All done! :humalon:')
        self.create_ami()

    def deploy_code(self):
        with cd("{}/{}".format(BASE_PATH, self.app_name)):
            with self._activate_virtualenv():
                run('git pull')
                run('pip install -r requirements.txt')

    def supervisor(self, task):
        for app_name in self.SUPERVISED_APPS:
            sudo('supervisorctl %s %s' % (task, app_name))

    def call_supervisor(self, task):
        execute(lambda: self.supervisor(task), hosts=self.private_ips)

    def create_ami(self):
        ami_decision = raw_input('\n Do you want new AMI? [Y/n]').lower() or 'y'
        if ami_decision != 'y':
            return

        for aws_name in self.aws_names:
            # =========== AMI ==============

            # print 'Creating AMI based on: {}'.format(name_tag)
            ec2_resource = EC2Resource(ec2_conn, [aws_name])
            private_ips, ids = ec2_resource.get_private_ips()
            if len(private_ips) > 1:
                print("Which machine you want to base new AMI on:")
                for i, (ip, instanceid) in enumerate(zip(private_ips, ids), start=1):
                    print "%d) %s (%s)\t" % (i, ip, instanceid)
                index = int(raw_input("Select number (default: 1): ") or 1) - 1
            else:
                index = 0
            try:
                ip = private_ips[index]
                instanceid = ids[index]
            except Exception as e:
                print 'no updates for u:', e
                return

            print 'New AMI will be based on machine %s (%s)' % (ip, instanceid)
            instance = ec2_resource.get_instance_by_id(instanceid)

            updater = AMIUpdater(ec2_conn, aws_name)
            default_name = updater.get_name()
            ami_name = raw_input('New AMI name (default "%s"): ' % default_name) or default_name
            print 'New name is', ami_name

            random_number = random.randint(100, 999)

            try:
                ami_id = updater.create_ami(instance.id, ami_name)
            except AMINameExists:
                print '! AMI name already exists, creating with additional random suffix {}'.format(random_number)
                ami_id = updater.create_ami(instance.id, "{}-{}".format(ami_name, random_number))

            # =========== AMI tags ==============

            # set tags to newly created ami
            tag_updater = TagUpdater(ec2_conn)
            try:
                tag_updater.set_tags(resource=ami_id,
                                     tags=tag_updater.create_tags_dict(name=ami_name, description=ami_name))
            except Exception as err:
                print 'AMI tagging error {}'.format(err)
                return

            print '--- New AMI created. ID: %s ---' % ami_id

            if has_autoscaling_conf(self.key):

                # =========== ASG init ==============

                asg_updater = ASGUpdater(autoscale_conn, aws_name)

                # =========== LC update ==============

                lc_updater = LaunchConfigurationUpdater(
                    autoscale_conn, aws_name, asg_updater.current_group.launch_config_name
                )
                name = raw_input('Provide new name for LC (default: %s): '
                                 % lc_updater.get_name()) or lc_updater.get_name()
                instance_type = raw_input('Provide new instance type (default: %s): '
                                          % instance.instance_type) or instance.instance_type

                try:
                    new_lc = lc_updater.update(ami_id, instance_type, name)
                except LCNameExists:
                    print '! LC name already exists, creating with additional random suffix {}'.format(random_number)
                    new_lc = lc_updater.update(ami_id, instance_type, "{}-{}".format(name, random_number))

                print '--- New LC created ---'

                # =========== ASG update ==============

                asg_instance = asg_updater.update(new_lc)

                print '--- ASG updated. Name: %s ---' % asg_instance.name

    def debug(self):
        print "key".ljust(20, '.') + self.key
        print "deploy name".ljust(20, '.') + self.deploy_name
        print "app name".ljust(20, '.') + self.app_name
        print "supervised apps".ljust(20, '.') + str(self.SUPERVISED_APPS)
        print "aws names".ljust(20, '.') + str(self.aws_names)
