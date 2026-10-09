import io
import zipfile

import pytest

from tactile_contact.source_archive import RangeReader, read_member


class Response(io.BytesIO):
    def __init__(self, body, status, content_range):
        super().__init__(body)
        self.status = status
        self.headers = {"Content-Range": content_range}


def opener_for(body, status=206, wrong_range=False):
    def open_request(request, timeout):
        start, end = map(int, request.headers["Range"].removeprefix("bytes=").split("-"))
        return Response(body[start:end+1], status, "wrong" if wrong_range else f"bytes {start}-{end}/{len(body)}")
    return open_request


def test_remote_zip_selected_member_and_budget():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("selected.csv", b"time,X\n0,1\n")
        archive.writestr("other.csv", b"unused")
    body = buffer.getvalue()
    reader = RangeReader("https://example.test/archive", len(body), budget=4096, opener=opener_for(body))
    with zipfile.ZipFile(reader) as archive:
        assert read_member(archive, archive.getinfo("selected.csv")) == b"time,X\n0,1\n"
        with pytest.raises(ValueError, match="bounded size"):
            read_member(archive, archive.getinfo("selected.csv"), max_bytes=2)
    assert 0 < reader.transferred < 4096
    with pytest.raises(ValueError, match="budget"):
        RangeReader("unused", 100, budget=2, opener=opener_for(b"a"*100)).read(3)


@pytest.mark.parametrize("status,wrong_range", [(200, False), (206, True)])
def test_ignored_or_inexact_range_rejected_before_body_read(status, wrong_range):
    class Unreadable(Response):
        def read(self, count=-1):
            raise AssertionError("Unbounded/invalid body must never be read")
    def opener(request, timeout):
        return Unreadable(b"", status, "wrong" if wrong_range else "bytes 0-1/2")
    with pytest.raises(ValueError, match="honor"):
        RangeReader("https://example.test/archive", 2, opener=opener).read(2)


def test_short_range_and_negative_seek_rejected():
    reader = RangeReader("https://example.test/archive", 3, opener=lambda request, timeout: Response(b"ab", 206, "bytes 0-2/3"))
    with pytest.raises(ValueError, match="length"):
        reader.read(3)
    with pytest.raises(ValueError, match="seek"):
        reader.seek(-1)


def test_corrupt_member_crc_is_rejected():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED) as archive:
        archive.writestr("selected.csv", b"time,X\n0,1\n")
    corrupt = buffer.getvalue().replace(b"time,X\n0,1\n", b"time,X\n0,9\n", 1)
    reader = RangeReader("https://example.test/archive", len(corrupt), opener=opener_for(corrupt))
    with zipfile.ZipFile(reader) as archive:
        with pytest.raises(zipfile.BadZipFile, match="CRC"):
            read_member(archive, archive.getinfo("selected.csv"))
