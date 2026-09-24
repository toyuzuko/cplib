from math import copysign, isnan
from pathlib import Path
from random import Random
import subprocess
import sys
import unittest
from unittest.mock import patch

import __pypy__  # type: ignore

from cplib.tools.fastio import FastIO


class ChunkReader:
    def __init__(self, data: bytes, sizes: tuple[int, ...]):
        self.data, self.sizes = data, sizes
        self.pos = self.calls = 0
    def __call__(self, fd: int, size: int) -> bytes:
        assert fd == 0
        size = min(size, self.sizes[self.calls % len(self.sizes)])
        self.calls += 1
        result = self.data[self.pos:self.pos+size]
        self.pos += len(result)
        return result


def fresh_io() -> type[FastIO]:
    class IO(FastIO):
        BUFFER_SIZE = 128
        RELOAD_THRESHOLD = 64
        ibuf = b''
        pil = pir = 0
        sb = __pypy__.builders.StringBuilder()
        registered = False
    return IO


class FastIOContractsTest(unittest.TestCase):
    def test_integers_and_short_reads(self) -> None:
        rng = Random(0)
        tokens = ['0', '-0', '+1', '-12', '0005', '1_234', str(10**300+7)]
        tokens += [str(rng.randrange(-10**30, 10**30)) for _ in range(300)]
        separators = [' ', '\n', '\t', '\r\n', '\v', '\f', '\x00', ' '*300]
        text = '\n'*257 + ''.join(token+rng.choice(separators) for token in tokens)
        for sizes in ((1,), (2,), (3, 1, 7), (64,), (127,), (4096,)):
            for trailing in (True, False):
                data = text.encode() if trailing else text.rstrip('\n\t\r\v\f\x00 ').encode()
                cls = fresh_io()
                with patch('cplib.tools.fastio.os.read', side_effect=ChunkReader(data, sizes)):
                    self.assertEqual(cls.read_ints(len(tokens)), tuple(map(int, tokens)))
                    for _ in range(2):
                        with self.assertRaises(EOFError):
                            cls.read_int()
        for threshold in (0, 1, 64, 1000):
            for cut in range(1, 30):
                cls = fresh_io()
                cls.RELOAD_THRESHOLD = threshold
                data = b'  -123 +456 789 00000000000100 -0'
                with patch('cplib.tools.fastio.os.read', side_effect=ChunkReader(data, (cut,))):
                    self.assertEqual(cls.read_ints(5), (-123, 456, 789, 100, 0))
        for token in ('-', '+', '12x', '1.2', '0xff', '_1', '1__2', 'abc'):
            cls = fresh_io()
            with patch('cplib.tools.fastio.os.read', side_effect=ChunkReader((token+' 7 ').encode(), (1,))):
                with self.assertRaises(ValueError):
                    cls.read_int()
                self.assertEqual(cls.read_int(), 7)
        cls = fresh_io()
        with patch('cplib.tools.fastio.os.read') as read:
            self.assertEqual(cls.read_ints(0), ())
            with self.assertRaises(ValueError):
                cls.read_ints(-1)
            read.assert_not_called()
        previous_limit = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(640)
            for size in (1, 1024):
                cls = fresh_io()
                cls.BUFFER_SIZE = 2048
                with patch('cplib.tools.fastio.os.read', side_effect=ChunkReader(b'9'*700+b' 7', (size,))):
                    with self.assertRaises(ValueError):
                        cls.read_int()
                    self.assertEqual(cls.read_int(), 7)
        finally:
            sys.set_int_max_str_digits(previous_limit)

    def test_float_conversion(self) -> None:
        rng = Random(0)
        tokens = ['0', '-0', '.12', '+.5', '1.', '1e-300', '-1e+300', '5e-324', '1e309', '-inf', 'nan', '1_000.25']
        tokens += [repr(rng.uniform(-1e200, 1e200)) for _ in range(300)]
        tokens += ['0.'+'0'*300+'12345', '1234567890.'+'1234567890'*30]
        for sizes in ((1,), (2, 7, 1), (64,), (1024,)):
            cls = fresh_io()
            with patch('cplib.tools.fastio.os.read', side_effect=ChunkReader(('  \n'+'\n'.join(tokens)).encode(), sizes)):
                for token in tokens:
                    expected, actual = float(token), cls.read_float()
                    if isnan(expected):
                        self.assertTrue(isnan(actual))
                    else:
                        self.assertEqual(actual, expected)
                        self.assertEqual(copysign(1., actual), copysign(1., expected))
                with self.assertRaises(EOFError):
                    cls.read_float()
        for token in (b'.', b'+', b'1e', b'1.2.3', b'word'):
            cls = fresh_io()
            with patch('cplib.tools.fastio.os.read', side_effect=ChunkReader(token+b' 2.5', (1,))):
                with self.assertRaises(ValueError):
                    cls.read_float()
                self.assertEqual(cls.read_float(), 2.5)

    def test_tokens_lines_and_eof(self) -> None:
        rng = Random(0)
        tokens = [''.join(rng.choice('abcdef123!+-') for _ in range(rng.randrange(1, 500))) for _ in range(100)]
        tokens.append('x'*200000)
        data = ('\n '*100+'\t\r\n'.join(tokens)).encode()
        for sizes in ((1, 7, 100), (64,), (1000000,)):
            cls = fresh_io()
            with patch('cplib.tools.fastio.os.read', side_effect=ChunkReader(data, sizes)):
                self.assertEqual([cls.read() for _ in tokens], tokens)
                with self.assertRaises(EOFError):
                    cls.read()
        lines = ['', ' ', '\r', 'abc\tdef\r', 'z'*200000, 'last line']
        for sizes in ((1, 7, 100), (64,), (1000000,)):
            cls = fresh_io()
            with patch('cplib.tools.fastio.os.read', side_effect=ChunkReader('\n'.join(lines).encode(), sizes)):
                self.assertEqual([cls.read_line() for _ in lines], lines)
                self.assertEqual(cls.read_line(), '')
                self.assertEqual(cls.read_line(), '')
                with self.assertRaises(EOFError):
                    cls.read()
        for sizes in ((1,), (1000,)):
            cls = fresh_io()
            with patch('cplib.tools.fastio.os.read', side_effect=ChunkReader(b'12 hello world\r\n\n-3\nend', sizes)):
                self.assertEqual(cls.read_int(), 12)
                self.assertEqual(cls.read(), 'hello')
                self.assertEqual(cls.read_line(), ' world\r')
                self.assertEqual(cls.read_line(), '')
                self.assertEqual(cls.read_int(), -3)
                self.assertEqual(cls.read_line(), '')
                self.assertEqual(cls.read_line(), 'end')
        for method in ('read', 'read_line'):
            cls = fresh_io()
            with patch('cplib.tools.fastio.os.read', side_effect=ChunkReader(b'\xff\nabc', (1,))):
                with self.assertRaises(UnicodeDecodeError):
                    getattr(cls, method)()
                self.assertEqual(cls.read(), 'abc')

    def test_load_retains_unread_input(self) -> None:
        cls = fresh_io()
        reader = ChunkReader(b'abcd ef\nlast', (4,))
        with patch('cplib.tools.fastio.os.read', side_effect=reader):
            cls.load()
            self.assertEqual(cls.ibuf, b'abcd')
            cls.load()
            self.assertEqual(cls.ibuf, b'abcd ef\n')
            self.assertEqual(cls.read(), 'abcd')
            cls.load()
            self.assertEqual(cls.ibuf, b' ef\nlast')
            self.assertEqual(cls.read(), 'ef')
            self.assertEqual(cls.read_line(), '')
            self.assertEqual(cls.read_line(), 'last')
        # A complete buffered token does not attempt a speculative read that
        # could block while an interactive input source waits for output.
        cls = fresh_io()
        cls.ibuf, cls.pir = b'123 ', 4
        with patch('cplib.tools.fastio.os.read', side_effect=AssertionError('unnecessary read')):
            self.assertEqual(cls.read_int(), 123)

    def test_output_partial_writes_and_registration(self) -> None:
        cls = fresh_io()
        written = bytearray()
        def write(fd: int, data: memoryview) -> int:
            self.assertEqual(fd, 1)
            size = min(3, len(data))
            written.extend(data[:size])
            return size
        with patch('cplib.tools.fastio.atexit.register') as register, patch('cplib.tools.fastio.os.write', side_effect=write) as output:
            cls.atexit_register()
            cls.atexit_register()
            cls.write('日本語')
            cls.writeln(' xyz')
            cls.flush()
            self.assertEqual(written, '日本語 xyz\n'.encode())
            calls = output.call_count
            cls.flush()
            self.assertEqual(output.call_count, calls)
            cls.write('next')
            cls.flush()
            self.assertEqual(written, '日本語 xyz\nnext'.encode())
            register.assert_called_once_with(cls.flush)
            register.call_args.args[0]()
            self.assertEqual(written, '日本語 xyz\nnext'.encode())
        cls = fresh_io()
        with patch('cplib.tools.fastio.atexit.register') as register:
            cls.writeln('a')
            cls.write('b')
            register.assert_called_once_with(cls.flush)

    def test_output_errors(self) -> None:
        for failure in (OSError('broken pipe'), 0):
            cls = fresh_io()
            cls.registered = True
            cls.write('abcdef')
            with patch('cplib.tools.fastio.os.write', side_effect=[2, failure]):
                with self.assertRaises(OSError):
                    cls.flush()
            with patch('cplib.tools.fastio.os.write') as output:
                cls.flush()
                output.assert_not_called()
        cls = fresh_io()
        cls.registered = True
        cls.write('\ud800')
        with self.assertRaises(UnicodeEncodeError):
            cls.flush()
        self.assertEqual(cls.sb.build(), '\ud800')

    def test_actual_process_streams(self) -> None:
        root = Path(__file__).resolve().parents[2]
        code = '''
from cplib.tools.fastio import FastIO
n = FastIO.read_int()
FastIO.writeln(str(sum(FastIO.read_ints(n))))
FastIO.flush()
FastIO.flush()
FastIO.write(FastIO.read())
FastIO.atexit_register()
'''
        result = subprocess.run([sys.executable, '-c', code], input=b'4\n1 -2 3 4\nend', capture_output=True, cwd=root, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'6\nend')


if __name__ == '__main__':
    unittest.main()
