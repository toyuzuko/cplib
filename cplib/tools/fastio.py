#!/usr/bin/env python3

import atexit
import os
import __pypy__  # pyright: ignore[reportMissingModuleSource]


class FastIO:
    """Buffered input/output for PyPy contest scripts.

    Class methods share input from file descriptor 0 and UTF-8 output to file
    descriptor 1. Do not mix these reads with another buffered stdin reader.
    Token separators are bytes at most 32; string reads require ASCII.
    The token readers leave the following separator unread, so read_line()
    immediately after a token returns the remainder of that same line.
    Input/output descriptors must be blocking. This class is not thread-safe.

    Space Complexity:
        O(BUFFER_SIZE + longest token or line + buffered output), under normal
        reads. Explicit load() calls also retain all unread input.

    Examples:
        >>> x = FastIO.read_int()
        >>> FastIO.writeln(str(x))
    """

    BUFFER_SIZE = 131072
    RELOAD_THRESHOLD = 64
    ibuf = bytes()
    pil = 0
    pir = 0
    sb = __pypy__.builders.StringBuilder()
    registered = False

    @classmethod
    def load(cls) -> None:
        """Read another block, retaining the unread input.

        Returns:
            None. At EOF, the unread suffix remains unchanged. A short read
            is allowed; it does not imply EOF unless it returns no bytes.

        Time Complexity:
            O(unread bytes + BUFFER_SIZE), excluding time waiting for input.

        Space Complexity:
            O(unread bytes + BUFFER_SIZE).
        """
        cls.ibuf = cls.ibuf[cls.pil:] + os.read(0, cls.BUFFER_SIZE)
        cls.pil = 0
        cls.pir = len(cls.ibuf)

    @classmethod
    def _read_token(cls) -> bytes:
        buffer, pos, end = cls.ibuf, cls.pil, cls.pir
        while True:
            while pos < end and buffer[pos] <= 32:
                pos += 1
            if pos < end:
                break
            cls.pil = pos
            cls.load()
            buffer, pos, end = cls.ibuf, 0, cls.pir
            if not end:
                raise EOFError('no more tokens')
        start = pos
        while pos < end and buffer[pos] > 32:
            pos += 1
        cls.pil = pos
        if pos < end:
            return buffer[start:pos]

        parts = [buffer[start:pos]]
        while True:
            cls.load()
            buffer, end = cls.ibuf, cls.pir
            pos = 0
            while pos < end and buffer[pos] > 32:
                pos += 1
            cls.pil = pos
            parts.append(buffer[:pos])
            if pos < end or not end:
                return b''.join(parts)

    @classmethod
    def read_int(cls) -> int:
        """Read one base-10 integer token.

        Returns:
            The next integer, parsed as by int(token, 10). An optional sign
            and large integers are supported, subject to the interpreter's
            integer-string conversion limit.

        Raises:
            EOFError: If no token remains.
            ValueError: If the consumed token is not a valid integer.

        Time Complexity:
            O(skipped separators + token length), plus integer conversion.
            Conversion of very large integers may be superlinear.

        Space Complexity:
            O(token length), plus the input buffer.
        """
        buffer, pos, end = cls.ibuf, cls.pil, cls.pir
        if end - pos >= cls.RELOAD_THRESHOLD:
            while pos < end and buffer[pos] <= 32:
                pos += 1
            negative = pos < end and buffer[pos] == 45
            if pos < end and buffer[pos] in (43, 45):
                pos += 1
            start = pos
            value = 0
            limit = min(end, start + 64)
            while pos < limit and 48 <= buffer[pos] <= 57:
                value = value * 10 + buffer[pos] - 48
                pos += 1
            if pos > start and pos < end and buffer[pos] <= 32:
                cls.pil = pos
                return -value if negative else value
        # The generic path handles split tokens, EOF, and Python's full
        # base-10 syntax without allocating tokens on the usual fast path.
        return int(cls._read_token())

    @classmethod
    def read_ints(cls, n: int) -> tuple[int, ...]:
        """Read n integer tokens.

        Args:
            n: Non-negative number of integers to read.

        Returns:
            A tuple of n integers. Zero returns () without consuming input.

        Raises:
            ValueError: If n is negative or a token is not a valid integer.
            EOFError: If fewer than n tokens remain. Earlier reads are consumed.

        Time Complexity:
            O(n) plus the total cost of read_int() calls.

        Space Complexity:
            O(n) references plus the integers and input buffer.
        """
        if n < 0:
            raise ValueError('n must be non-negative')
        return tuple(cls.read_int() for _ in range(n))

    @classmethod
    def read_float(cls) -> float:
        """Read a floating-point token with Python's float conversion.

        Returns:
            The next float. Decimal and scientific notation, signs, inf, and
            nan are accepted, as by float(token).

        Raises:
            EOFError: If no token remains.
            ValueError: If the consumed token is not a valid float.

        Time Complexity:
            O(skipped separators + token length), plus float conversion.

        Space Complexity:
            O(token length), plus the input buffer.
        """
        return float(cls._read_token())

    @classmethod
    def read(cls) -> str:
        """Read one ASCII token, skipping leading separators.

        Returns:
            A non-empty ASCII token. Bytes at most 32 are separators.

        Raises:
            EOFError: If no token remains.
            UnicodeDecodeError: If the consumed token is not ASCII.

        Time Complexity:
            O(skipped separators + token length).

        Space Complexity:
            O(token length), plus the input buffer.
        """
        return cls._read_token().decode('ascii')

    @classmethod
    def read_line(cls) -> str:
        """Read the remainder of the current ASCII line.

        Returns:
            Text up to the next LF, excluding that LF but retaining CR and
            other whitespace. The LF is consumed. At EOF, returns the final
            unterminated line, or '' if nothing remains. Blank lines also
            return ''.

        Raises:
            UnicodeDecodeError: If the consumed line is not ASCII.

        Time Complexity:
            O(line length), excluding time waiting for input.

        Space Complexity:
            O(line length), plus the input buffer.
        """
        buffer, start = cls.ibuf, cls.pil
        pos = buffer.find(b'\n', start)
        if pos >= 0:
            cls.pil = pos + 1
            return buffer[start:pos].decode('ascii')
        parts = [buffer[start:]]
        cls.pil = cls.pir
        while True:
            cls.load()
            buffer = cls.ibuf
            pos = buffer.find(b'\n')
            if pos >= 0:
                cls.pil = pos + 1
                parts.append(buffer[:pos])
                break
            parts.append(buffer)
            cls.pil = cls.pir
            if not buffer:
                break
        return b''.join(parts).decode('ascii')

    @classmethod
    def write(cls, x: str) -> None:
        """Append text to the output buffer.

        Args:
            x: Text to encode as UTF-8 when flushed.

        Returns:
            None. Registers automatic flushing at exit on the first write.

        Time Complexity:
            O(len(x)).

        Space Complexity:
            O(len(x)) additional buffered output.
        """
        if not cls.registered:
            cls.atexit_register()
        cls.sb.append(x)

    @classmethod
    def writeln(cls, x: str) -> None:
        """Append text and an LF to the output buffer.

        Args:
            x: Text to encode as UTF-8 when flushed.

        Returns:
            None. Registers automatic flushing at exit on the first write.

        Time Complexity:
            O(len(x)).

        Space Complexity:
            O(len(x)) additional buffered output.
        """
        if not cls.registered:
            cls.atexit_register()
        cls.sb.append(x)
        cls.sb.append('\n')

    @classmethod
    def flush(cls) -> None:
        """Write buffered text to file descriptor 1 as UTF-8.

        Returns:
            None. Empties the buffer, so repeated flushes do not duplicate
            output. Handles partial writes on the blocking descriptor.

        Raises:
            OSError: If writing fails. A prefix may already have been written;
                the buffer is consumed and is not automatically retried.
            UnicodeEncodeError: If buffered text cannot be encoded as UTF-8.
                In this case the buffer is retained.

        Time Complexity:
            O(buffered output size), excluding time blocked on output.

        Space Complexity:
            O(encoded output size).
        """
        data = cls.sb.build().encode('utf-8')
        cls.sb = __pypy__.builders.StringBuilder()
        if not data:
            return
        view = memoryview(data)
        pos = 0
        while pos < len(data):
            written = os.write(1, view[pos:])
            if written <= 0:
                raise OSError('write made no progress')
            pos += written

    @classmethod
    def atexit_register(cls) -> None:
        """Register this class's flush method once for process exit.

        Returns:
            None. Repeated calls have no effect.

        Time Complexity:
            O(1).

        Space Complexity:
            O(1).
        """
        if not cls.registered:
            atexit.register(cls.flush)
            cls.registered = True
