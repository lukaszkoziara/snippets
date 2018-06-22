from boto.exception import EC2ResponseError


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
