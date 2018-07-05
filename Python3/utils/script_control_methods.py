import sys


def ask(question, default='y'):
    """Yes/No input getter

    Args:
        question (str): question, eg. 'Are You sure?'
        default (str): default answer, eg. 'y'

    Usage:
        if not ask('Continue?', 'n'):
            sys.exit()
    """
    upper_default = '[Y/n]' if default == 'y' else '[y/N]'

    resp = input(question + (' {} (default: {})'.format(upper_default, default))).lower()
    if resp not in ['y', 'n', '']:
        print('what?')
        return ask(question)
    return resp == 'y' or (resp == '' and default == 'y')


def chunks_gen(elements, output_size=100):
    """Yield successive n-sized chunks from l.

    Args:
        elements (iter): iterable with many elements, eg. [1,2,3]
        output_size (int): batch size, eg. 100
    """
    for i in range(0, len(elements), output_size):
        yield elements[i:i + output_size]


class ProgressBar:
    """Progress bar class

    Args:
        all_count: number of all elements
    """

    def __init__(self, all_count):
        self.percent = 0
        self.all_count = float(all_count)

    def show_progress(self, progress_count):
        """prepare current progress status
        """
        result = int(progress_count / self.all_count * 100)
        if result >= self.percent:
            self.percent = result
            sys.stdout.write('\r{} {}%\r'.format('{}'.format('#' * self.percent).ljust(100, '-'), self.percent))

            if self.percent >= 100:
                sys.stdout.write('')  # go to newline

            sys.stdout.flush()
