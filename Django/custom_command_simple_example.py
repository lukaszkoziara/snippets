# python 2
from urlparse import urlparse

from pages.models import Page
from utils.functions import cachalot_remover
from custom_command_simple import ProcessCommand


class Command(ProcessCommand):
    help = 'Updates page urls - from: //www.sth to: scheme://www.sth'
    queryset = Page.objects.filter(url__startswith='//')

    @cachalot_remover
    def process_method(self, model_ids=(), process_number=0):
        query = Page.objects.filter(id__in=model_ids)
        all = query.count()
        now = 0
        for page in query.iterator():
            print "__%d__: %d/%d" % (process_number, now, all)

            new_url = u"{}:{}".format(urlparse(page.original_url).scheme, page.url)
            Page.objects.filter(pk=page.pk).update(url=new_url)

            now += 1
