import logging as log
import subprocess


logger = log.getLogger('myapp')
hdlr = log.FileHandler('/path/to/file.log')
formatter = log.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(log.DEBUG)


def clamscan_scan_file(self, filename):
    logger.info("Scanning file with clamscan for: {}".format(filename))
    sys_out = ''

    try:
        sys_out = subprocess.check_output(
            'clamscan --max-filesize=600M --max-scansize=600M {}'.format(filename), shell=True
        )
    except subprocess.CalledProcessError as err:
        logger.error(
            'Calling subprocess with clamscan error: {}. (Maybe clamscan is not installed?)'.format(err.output),
            exc_info=True
        )
        return True

    sys_out = str(sys_out, 'utf-8')

    if sys_out and 'Infected files' in sys_out:
        logger.info("Extracting scanned files info for file: {}".format(filename))
        # extract info about scanned files
        scanned_files = sys_out[sys_out.find('Scanned files') + 15:]
        scanned_files = int(scanned_files[:scanned_files.find('\n')])
        if not scanned_files:
            logger.error('System did not scan file: {}'.format(filename))
        else:
            # extract info about infected files
            infected_files = sys_out[sys_out.find('Infected files') + 16:]
            infected_files = int(infected_files[:infected_files.find('\n')])
            if infected_files:
                log.warning('Found infected file: {}'.format(filename))
                return False
    else:
        logger.error('There is problem with scanning file: {} with system output: {}'.format(filename, sys_out))
    return True