# python 2
from multiprocessing import Process

from django.core.management.base import BaseCommand
from django.db import connection

from utils.functions import cachalot_remover


class ProcessCommand(BaseCommand):
    """Custom management command
    Script splits available primary keys and distribute them to separeted processes
    """

    help = 'Some description'
    queryset = None
    process_count = 4
    process_method_name = 'process_method'

    @cachalot_remover
    def process_method(self, model_ids=(), process_number=0, *args, **kwargs):
        """Main management command method

        Args:
            model_ids (list): list of ids
            process_number (int): number of process
        """
        pass

    @cachalot_remover
    def handle(self, *args, **options):
        # prepare query ids
        model_ids = list(self.queryset.values_list('pk', flat=True))
        delta = (len(model_ids) / self.process_count) + 1
        connection.close()

        # spawn processes
        for it in range(0, self.process_count):
            args = (model_ids[it * delta:(it + 1) * delta], it + 1) + args
            Process(
                target=getattr(self, self.process_method_name),
                args=(model_ids[it*delta:(it+1)*delta], it+1),
                kwargs=options
            ).start()
