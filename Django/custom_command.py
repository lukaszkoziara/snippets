# python3
import datetime
import os
import time

from django.conf import settings as dj_settings
from django.core.management.base import BaseCommand

from utils import readable_time, timestamped_filename


class CustomBaseCommand(BaseCommand):
    script_name = 'default'
    errors_file_name = 'default'

    def check_exitcodes_finished(self, exitcodes):
        for elem in exitcodes:
            if elem is None or elem > 0:
                return False
        return True

    def handle(self, *args, **options):
        """base handle method
        """

        # prepare options
        self.debug = options.get('debug', False)

        # create directories and files names
        os.makedirs(os.path.join(dj_settings.SCRIPT_FILES_PATH), exist_ok=True)
        self.errors_file_name = timestamped_filename(dj_settings.SCRIPT_FILES_PATH, self.script_name)

        # prepare data for stats
        start_time = time.time()
        start_date_and_time = datetime.datetime.now()

        # main handle call
        self.main_handle(*args, **options)

        # summary info data
        end_time = time.time()
        end_date_and_time = datetime.datetime.now()
        elapsed_time = end_time - start_time
        elapsed_time_str = readable_time(elapsed_time)

        # write summary to file
        result_summary_file_path = os.path.join(dj_settings.SCRIPT_FILES_PATH, 'summary_info_{}_{}.txt'.format(
            self.script_name, start_date_and_time.strftime(dj_settings.DT_FILE_FORMAT)
        ))

        with open(result_summary_file_path, 'w') as result_file:
            result_file.write('{:*^30}\n'.format(' Summary '))
            result_file.write('Start time: {}\n'.format(start_date_and_time.strftime(dj_settings.DT_FORMAT)))
            result_file.write('End time: {}\n'.format(end_date_and_time.strftime(dj_settings.DT_FORMAT)))
            result_file.write('Elapsed in: {}\n'.format(elapsed_time_str))

    def main_handle(self, *args, **kwargs):
        pass