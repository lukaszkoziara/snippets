from urllib.parse import urlparse


def check_aws_url(url, bucket_name):
    if url.find('{}.s3.amazonaws.com'.format(bucket_name)) > -1:
        return True
    if url.find('s3-eu-west-1.amazonaws.com/{}'.format(bucket_name)) > -1:
        return True
    return False


def get_name_from_s3_url(url):
    parsed = urlparse(url)
    base_path = parsed.path.split('%2')[0]  # url path contains encoded ','
    return base_path.split('/')[-1]
