#!/usr/bin/env python3

import iroiro
import threading
import queue
import random


def worker(q, name):
    import time
    for i in range(100):
        time.sleep(random.random() / 3)
        q.put(name)


def main():
    names = ['wah', 'wow', 'foo', 'bar', 'baz']

    pba = iroiro.ProgressBarArray()
    q = queue.Queue()

    with pba:
        progress = {name: 0 for name in names}
        threads = [threading.Thread(target=worker, args=(q, name), daemon=True) for name in names]

        for t in threads:
            t.start()

        while True:
            event = q.get()
            progress[event] += 1
            pba[event] = f'{event} {progress[event]} / 100'

            if sum(progress.values()) == len(names) * 100:
                break

    for t in threads:
        t.join()


if __name__ == '__main__':
    main()
