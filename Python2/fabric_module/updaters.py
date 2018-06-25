from collections import namedtuple
from datetime import datetime
from itertools import groupby

from boto.exception import EC2ResponseError, BotoServerError

from common import admin_connection


LCRecord = namedtuple('LCRecord', ['lc', 'group', 'date'])
group_regexp = re.compile(r'Humalo-(\w+-\w+)-')


class EC2Resource:
    TEMPLATE = u'Humalo-{aws_name}-EC2-EUw1'

    def __init__(self, ec2_conn, aws_names):
        self.ec2_conn = ec2_conn
        self.aws_names = aws_names

    def get_private_ips(self):
        if not self.aws_names:
            return [], []
        else:
            reservations = []
            for aws_name in self.aws_names:
                reservations += self.ec2_conn.get_all_instances(
                    filters={"tag:Name": self.TEMPLATE.format(aws_name=aws_name), "tag:Project": 'Humalo'}
                )

            results = zip(
                *[(i.private_ip_address, i.id) for r in reservations for i in r.instances if i.state == 'running'])

            if not results:
                print "No IPs found for AWS names: '{}'.".format(self.aws_names)
                return [], []
            else:
                return results

    def get_instance_by_id(self, instance_id):
        try:
            reservations = self.ec2_conn.get_all_instances(instance_ids=[instance_id])
            return reservations[0].instances[0]
        except EC2ResponseError:
            return None


class AMINameExists(Exception):
    pass


class AMIUpdater:
    TEMPLATE = u'Humalo-{aws_name}-AMI-EUw1-{stamp.year}-{stamp.month}-{stamp.day}'

    def __init__(self, ec2_conn, aws_name):
        self.ec2_conn = ec2_conn
        self.aws_name = aws_name

    def get_name(self):
        return self.TEMPLATE.format(aws_name=self.aws_name, stamp=datetime.now())

    def create_ami(self, instance_id, ami_name):
        try:
            return self.ec2_conn.create_image(instance_id, ami_name, description=ami_name)
        except EC2ResponseError:
            raise AMINameExists


class TagUpdater:
    def __init__(self, connection):
        self.connection = connection

    def create_tags_dict(self, name, description, project='Humalo'):
        return {
            'Name': name,
            'Description': description,
            'Project': project
        }

    def set_tags(self, resource, tags):
        self.connection.create_tags(resource, tags)


class ASGUpdater:
    TEMPLATE = u'Humalo-{aws_name}-EC2-EUw1'

    def __init__(self, autoscale_conn, aws_name):
        self.autoscale_conn = autoscale_conn
        self.aws_name = aws_name
        try:
            self.current_group = next(
                g for g in self.autoscale_conn.get_all_groups() if self.get_group_name(g) == self.get_name()
            )
        except IndexError:
            self.current_group = None
            raise Exception("There's no group tagged as %s" % self.get_name())

    def get_name(self):
        return self.TEMPLATE.format(aws_name=self.aws_name)

    def get_group_name(self, g):
        return next(tag.value for tag in g.tags if tag.key == 'Name')

    def update(self, launch_config):
        self.current_group.launch_config_name = launch_config.name
        self.current_group.update()
        return self.current_group


class LaunchConfigurationUpdater:
    TEMPLATE = u'Humalo-{aws_name}-LaunchConf-EUw1'

    def __init__(self, autoscale_conn, aws_name, config_name):
        self.autoscale_conn = admin_connection()
        self.aws_name = aws_name
        self.config_name = config_name

    def get_name(self, with_date=True):
        main_template = self.TEMPLATE.format(aws_name=self.aws_name)
        if with_date:
            today = datetime.now()
            main_template = u'{main_name}-{date.year}-{date.month}-{date.day}'.format(main_name=main_template,
                                                                                     date=today)
        return main_template

    def delete_stale_launch_confs(self, lcs):
        confs = []
        for lc in lcs:
            try:
                confs.append(LCRecord(lc, get_group(lc), get_ord(lc)))
            except:
                pass
        stale_confs = get_stale_confs(confs)
        if not stale_confs:
            return
        print 'stale Launch configurations detected:'
        for group, confs in stale_confs:
            print '\t* %s: %d' % (group, len(confs))
        if ask('Show more details?', 'n'):
            print_confs(stale_confs)
        if not ask('Do you want to delete stale launch confs?', 'n'):
            return
        for g, confs in stale_confs:
            for conf in confs[:-1]:
                print 'deleting', conf.lc.name
                conf.lc.delete()

    def update(self, ami_id, instance_type, name):
        lcs = self.autoscale_conn.get_all_launch_configurations(names=[self.config_name])
        self.delete_stale_launch_confs(self.autoscale_conn.get_all_launch_configurations())
        try:
            current_lc = lcs[0]
        except IndexError:
            raise Exception(
                "dafug, I haven't found any LaunchConfigurations with name %s" % repr(self.config_name))

        new_lc = boto.ec2.autoscale.LaunchConfiguration(name=name,
                                                        image_id=ami_id,
                                                        key_name=current_lc.key_name,
                                                        security_groups=current_lc.security_groups,
                                                        instance_type=instance_type,
                                                        instance_monitoring=current_lc.instance_monitoring)
        try:
            self.autoscale_conn.create_launch_configuration(new_lc)
        except BotoServerError:
            raise LCNameExists
        return new_lc


def get_group(lc):
    return group_regexp.match(lc.name).group(1)


def get_stale_confs(lcs):
    by_group = lambda lc: lc.group
    lcs = sorted(lcs, key=lambda lc: (lc.group, lc.date))
    grouped_lcs = [(group, list(confs)) for group, confs in groupby(lcs, key=by_group)]
    return [(key, val) for key, val in grouped_lcs if len(val) > 4]


class LCNameExists(Exception):
    pass


def ask(question, default='y'):
    resp = raw_input(question + (' [Y/n] (default: %s)' % default)).lower()
    if resp not in ['y', 'n', '']:
        print 'what?'
        return ask(question)
    return resp == 'y' or (resp == '' and default == 'y')


def print_confs(grouped_lcs):
    print
    for group, confs in grouped_lcs:
        print group
        stale_confs = confs[:-1]  # leave most recent one
        for conf in stale_confs:
            print '\t- %s' % conf.lc.name
        print '\t+ %s' % confs[-1].lc.name
