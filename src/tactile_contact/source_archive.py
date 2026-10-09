"""Read selected ZIP members over validated, byte-budgeted HTTP ranges.

No full-archive fallback: an ignored Range header fails before reading a body.
Member CRC is checked by zipfile; this does not verify the full archive MD5.
"""
from __future__ import annotations

import io
import urllib.request


class RangeReader(io.RawIOBase):
    def __init__(self, url, size, budget=32 * 1024**2, opener=None):
        self.url, self.size, self.budget = url, size, budget
        self.position, self.transferred = 0, 0
        self.opener = opener or urllib.request.urlopen
        self.ranges = []

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        target = offset + (0 if whence == 0 else self.position if whence == 1 else self.size if whence == 2 else -1)
        if whence not in (0, 1, 2) or target < 0:
            raise ValueError("Invalid archive seek")
        self.position = target
        return target

    def read(self, count=-1):
        count = max(0, min(self.size-self.position, self.size if count < 0 else count))
        if count == 0:
            return b""
        if self.transferred + count > self.budget:
            raise ValueError("Archive byte budget exceeded")
        start, end = self.position, self.position+count-1
        request = urllib.request.Request(self.url, headers={"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"})
        with self.opener(request, timeout=30) as response:
            expected = f"bytes {start}-{end}/{self.size}"
            if response.status != 206 or response.headers.get("Content-Range") != expected:
                raise ValueError("Server did not honor exact bounded Range request")
            body = response.read(count+1)
        if len(body) != count:
            raise ValueError("Range body length mismatch")
        self.transferred += count
        self.ranges.append([start, end])
        self.position += count
        return body


def read_member(archive, info, max_bytes=8 * 1024**2):
    if info.file_size > max_bytes or info.compress_size > max_bytes:
        raise ValueError("ZIP member exceeds bounded size")
    with archive.open(info) as stream:
        body = stream.read(max_bytes+1)
    if len(body) != info.file_size or len(body) > max_bytes:
        raise ValueError("ZIP member size mismatch")
    return body
