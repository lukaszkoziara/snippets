import multiprocessing
import random
import time


def worker(proc_num, lock_mgr, result_list):
    """worker method
    """
    time.sleep(random.randint(0, 3))
    rrand = random.randint(0, 2)

    print('{}: {}'.format(proc_num, rrand))

    if str(rrand) in lock_mgr:
        print('{}: lock'.format(proc_num))
    else:
        print('{}: locking'.format(proc_num))

        lock_mgr[str(rrand)] = True
        time.sleep(3)
        del lock_mgr[str(rrand)]
        result_list.append(rrand)

    print('{}: {}'.format(proc_num, lock_mgr.keys()))


if __name__ == '__main__':
    # prepare dict manager
    dict_manager = multiprocessing.Manager()
    lock_mgr = dict_manager.dict()

    # prepare list manager
    list_manager = multiprocessing.Manager()
    result_list = list_manager.list()

    # spawn processes
    jobs = []
    for it in range(5):
        proc = multiprocessing.Process(target=worker, args=(it, lock_mgr, result_list))
        jobs.append(proc)
        proc.start()

    for proc in jobs:
        proc.join()

    # show summary
    print('=' * 10)
    print('Lock manager values: {}'.format(lock_mgr.values()))
    print('list manager sum: {}'.format(sum(result_list)))
    print('=' * 10)
