import threading

from .lib_test_utils import *

import iroiro as iro

class TestRunInThread(TestCase):
    def test_run_in_thread(self):
        barrier = threading.Barrier(2)
        checkpoint = False

        def may_stuck():
            nonlocal checkpoint
            barrier.wait()
            checkpoint = True

        with self.run_in_thread(may_stuck):
            self.false(checkpoint)
            barrier.wait()

        self.true(checkpoint)

    def test_run_in_thread_reuse(self):
        def foo():
            pass

        p = self.run_in_thread(foo)
        with p:
            pass

        with self.raises(RuntimeError):
            with p:
                pass


class TestCheckPoint(TestCase):
    def test_checkpoint(self):
        Checkpoint = iro.Checkpoint

        checkpoint = Checkpoint(self)

        self.false(checkpoint)
        checkpoint.set()
        checkpoint.check()
        checkpoint.check(True)
        self.true(checkpoint)

        checkpoint.clear()
        checkpoint.check(False)
        self.false(checkpoint)

        def set_checkpoint():
            checkpoint.wait()

        with self.run_in_thread(set_checkpoint):
            checkpoint.set()

        checkpoint.check()


class TestSubprocRunMocker(TestCase):
    def test_mock_basic(self):
        mock_run = RunMocker()
        def mock_wah(proc, *args):
            proc.stdout.writeline('mock wah')
            if args:
                proc.stdout.writeline(' '.join(args))
            return 0
        mock_run.register('wah', mock_wah)

        p = mock_run('wah'.split())
        self.eq(p.stdout.lines, ['mock wah'])

        p = mock_run('wah')
        self.eq(p.stdout.lines, ['mock wah'])

        p = mock_run('wah wah wah'.split())
        self.eq(p.stdout.lines, ['mock wah', 'wah wah'])

    def test_mock_meaningless_mock(self):
        mock_run = RunMocker()
        with self.raises(ValueError):
            mock_run.register('cmd')

    def test_mock_ambiguous_mock(self):
        mock_run = RunMocker()
        with self.raises(ValueError):
            mock_run.register('wah', lambda: None, stdout='wah')

    def test_mock_cmd_with_wrong_type(self):
        mock_run = RunMocker()
        with self.raises(ValueError):
            mock_run.register(['wah'], lambda proc: 0)

    def test_mock_callback_with_wrong_type(self):
        mock_run = RunMocker()
        with self.raises(TypeError):
            mock_run.register('wah', 0)

    def test_mock_run_empty_cmd(self):
        mock_run = RunMocker()
        with self.raises(ValueError):
            mock_run([])

    def test_mock_run_unregistered_cmd(self):
        mock_run = RunMocker()
        with self.raises(ValueError):
            p = mock_run('ls -a -l'.split())

    def test_mock_register_default_cmd(self):
        mock_run = RunMocker()
        def default_cmd(proc, *args):
            self.eq(args, ('-a', '-l'))
            return 42
        mock_run.register('*', default_cmd)
        p = mock_run('ls -a -l'.split())
        self.eq(p.returncode, 42)

    def test_mock_with_returncode(self):
        mock_run = RunMocker()
        mock_run.register('wah', returncode=1)
        p = mock_run(['wah'])
        self.eq(p.returncode, 1)

    def test_mock_with_stdout_stderr_returncode(self):
        mock_run = RunMocker()
        mock_run.register('wah',
                      stdout=['wah', 'wah wah', 'wah wah wah'],
                      stderr=['WAH', 'WAH WAH', 'WAH WAH WAH'],
                      returncode=520)

        p = mock_run(['wah'])
        self.eq(p.stdout.lines, ['wah', 'wah wah', 'wah wah wah'])
        self.eq(p.stderr.lines, ['WAH', 'WAH WAH', 'WAH WAH WAH'])
        self.eq(p.returncode, 520)

    def test_mock_with_stdout_stderr_returncode_side_effect(self):
        mock_run = RunMocker()
        mock_run.register('wah',
                      stdout=['wah1'],
                      stderr=['WAH1'],
                      returncode=42)
        mock_run.register('wah',
                      stdout=['wah2'],
                      stderr=['WAH2'],
                      returncode=43)

        p = mock_run(['wah'])
        self.eq(p.stdout.lines, ['wah1'])
        self.eq(p.stderr.lines, ['WAH1'])
        self.eq(p.returncode, 42)

        p = mock_run(['wah'])
        self.eq(p.stdout.lines, ['wah2'])
        self.eq(p.stderr.lines, ['WAH2'])
        self.eq(p.returncode, 43)

    def test_mock_side_effect(self):
        mock_run = RunMocker()

        def mock_ls_1st(proc, *args):
            self.eq(args, ('-a', '-l'))
            proc.stdout.writeline('file1')
        def mock_ls_3rd(proc, *args):
            self.eq(proc.cmd, ('ls', '-a', '-l', '--wah'))
            self.eq(args, ('-a', '-l', '--wah'))
            proc.stdout.writeline('file3')
        mock_run.register('ls', mock_ls_1st)
        mock_run.register('ls', stdout=['wah'], stderr=['WAH'], returncode=42)
        mock_run.register('ls', mock_ls_3rd)
        mock_run.register('ls', ValueError('ls is called too many times'))

        p = mock_run('ls -a -l'.split())
        self.eq(p.returncode, None)
        self.eq(p.stdout.lines, ['file1'])

        p = mock_run('ls -a -l'.split())
        self.eq(p.returncode, 42)
        self.eq(p.stdout.lines, ['wah'])
        self.eq(p.stderr.lines, ['WAH'])

        p = mock_run('ls -a -l --wah'.split())
        self.eq(p.returncode, None)
        self.eq(p.stdout.lines, ['file3'])

        with self.raises(ValueError):
            p = mock_run('ls -a -l --wah'.split())
