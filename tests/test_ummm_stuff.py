import struct

import pytest

from parsita import Failure, GeneralParsers, Success, eof, pred, reg, rep, success, until, Parser

from parsita.parsers import rep_n

# Not sure where these tests are supposed to go (if anywhere)


def utf_string_parser(length: int) -> Parser:
    if length == 0:
        return success("")
    elif length > 0:
        string_parser = rep(ByteParsers.byte, min=length - 1, max=length - 1) > (lambda x: b"".join(x).decode("utf-8"))
        null_parser = pred(ByteParsers.byte, lambda x: x == b"\x00", description="1-byte null padding")
        return string_parser << null_parser

    length = -2 * (length)
    string_parser = rep(ByteParsers.byte, min=length - 2, max=length - 2) > (lambda x: b"".join(x).decode("utf-16"))

    null_parser = pred(
        ByteParsers.byte & ByteParsers.byte, lambda x: x == [b"\x00", b"\x00"], description="2-byte null padding"
    )
    return string_parser << null_parser


class ByteParsers(GeneralParsers):
    byte = reg(b"[\x00-\xff]")

    numeric_byte = byte > (lambda x: int(struct.unpack("<b", x)[0]))
    int32 = rep_n(byte, n=4) > (lambda x: struct.unpack("<i", b"".join(x))[0])
    long = rep_n(byte, n=8) > (lambda x: struct.unpack("<q", b"".join(x))[0])
    float32 = rep_n(byte, n=4) > (lambda x: struct.unpack("<f", b"".join(x))[0])
    string = int32 >= utf_string_parser


class SaveFileHeaderParser(GeneralParsers):
    save_header_version = ByteParsers.int32
    save_version = ByteParsers.int32
    build_version = ByteParsers.int32
    map_name = ByteParsers.string
    map_options = ByteParsers.string
    session_name = ByteParsers.string
    played_seconds = ByteParsers.int32
    save_timestamp_ticks = ByteParsers.long
    session_visibility = ByteParsers.numeric_byte
    editor_object_version = ByteParsers.int32
    mod_metadata = ByteParsers.string
    mod_flags = ByteParsers.int32
    save_identifier = ByteParsers.string

    save_file_header = (
        save_header_version
        & save_version
        & build_version
        & map_name
        & map_options
        & session_name
        & played_seconds
        & save_timestamp_ticks
        & session_visibility
        & editor_object_version
        & mod_metadata
        & mod_flags
        & save_identifier << until(eof)
    )


def test_header_parse():
    sample_data = (
        b"\n\x00\x00\x00$\x00\x00\x00\x7f;\x03\x00\x11\x00\x00\x00Persistent_Level\x00?\x00\x00\x00?"
        b"startloc=DuneDesert?sessionName=GO!?Visibility=SV_FriendsOnly\x00\x04\x00\x00\x00GO!\x00>\x9a"
        b"\x10\x00\xd0\xf7}\xdaj^\xdb\x08\x01(\x00\x00\x00\x11\x00\x00\x00INVALID_METADATA\x00\x00\x00"
        b"\x00\x00\x17\x00\x00\x006em6Osmf-kSTmoAJCLsMbg\x00\xc1\x83*\x9e\x00\x00\x00\x00\x00\x00\x02\x00"
        b"\x00\x00\x00\x00]E\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00]E\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x02\x00\x00\x00\x00\x00x\x9c\xed}\x07T\x13\xcb\xfbv\x10A\x14+\x16\x8a\r\x11\x15\x01"
        b"!\xbd@\xb2\x03Rv\xec\xa8X\xb0"
    )

    header = SaveFileHeaderParser.save_file_header.parse(sample_data)
    print(header)
    assert isinstance(header, Success)
    print(header)


def test_header_parse_failure():
    sample_data = (
        b"\n\x00\x00\x00$\x00\x00\x00\x7f;\x03\x00\x11\x00\x00\x00Persistent_Level\x00?\x00\x00\x00?"
        b"startloc=DuneDesert?sessionName=GO!?Visibility=SV_FriendsOnly\x01\x04\x00\x00\x00GO!\x00>\x9a"
        b"\x10\x00\xd0\xf7}\xdaj^\xdb\x08\x01(\x00\x00\x00\x11\x00\x00\x00INVALID_METADATA\x00\x00\x00"
        b"\x00\x00\x17\x00\x00\x006em6Osmf-kSTmoAJCLsMbg\x00\xc1\x83*\x9e\x00\x00\x00\x00\x00\x00\x02\x00"
        b"\x00\x00\x00\x00]E\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00]E\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x02\x00\x00\x00\x00\x00x\x9c\xed}\x07T\x13\xcb\xfbv\x10A\x14+\x16\x8a\r\x11\x15\x01"
        b"!\xbd@\xb2\x03Rv\xec\xa8X\xb0"
    )

    # for coverage purposes
    header = SaveFileHeaderParser.save_file_header.parse(sample_data)
    assert isinstance(header, Failure)
    failure_message = repr(header)
    assert "1-byte null padding" in failure_message


def test_byte():
    value = 97
    tmp_value = struct.pack("<b", value)
    actual = ByteParsers.byte.parse(tmp_value)
    expected = b"a"
    assert actual == Success(expected)


def test_numeric_byte():
    value = 97
    tmp_value = struct.pack("<b", value)
    actual = ByteParsers.numeric_byte.parse(tmp_value)
    assert actual == Success(value)


def test_int32():
    value = 2147483647
    tmp_value = struct.pack("<i", value)
    actual = ByteParsers.int32.parse(tmp_value)
    assert actual == Success(value)


def test_long():
    value = 9223372036854775807
    tmp_value = struct.pack("<q", value)
    actual = ByteParsers.long.parse(tmp_value)
    assert actual == Success(value)


def test_float32():
    value = -12.345
    tmp_value = struct.pack("<f", value)
    actual = ByteParsers.float32.parse(tmp_value)

    import math

    assert math.isclose(value, actual.value_or(None), abs_tol=0.000001)


def test_utf8_string():
    value = "Hello Massage-2(A-B)b"
    length = len(value) + 1
    value_bytes = value.encode("utf-8")
    tmp_value = struct.pack("<i", length) + value_bytes + b"\x00"
    actual = ByteParsers.string.parse(tmp_value)
    assert actual == Success(value)


def test_utf16_string():
    value = "Hello Massage-2(A-B)b"
    length = len(value) + 2
    value_bytes = value.encode("utf-16")
    tmp_value = struct.pack("<i", -length) + value_bytes + b"\x00\x00"
    actual = ByteParsers.string.parse(tmp_value)
    assert actual == Success(value)


def test_utf16_string_fail_on_padding():
    value = "Hello Massage-2(A-B)b"
    value_bytes = value.encode("utf-16")
    bad_null_padding = b"\x00\x01"
    length = len(value_bytes) + len(bad_null_padding)
    coded_length_as_int = int(-(length / 2))
    length_bytes = struct.pack("<i", coded_length_as_int)
    tmp_value = length_bytes + value_bytes + bad_null_padding
    actual = ByteParsers.string.parse(tmp_value)
    assert isinstance(actual, Failure)
    failure_message = repr(actual)
    assert "2-byte null padding" in failure_message


# here for coverage purposes
def test_bytes_reader_exception():
    from parsita.state import BytesReader

    br = BytesReader("test_message")
    assert pytest.raises(TypeError, br.get_error_feedback_for_bytes)


def test_bytes_reader_hitting_eof_early():
    class TstParser(GeneralParsers):
        test = rep_n(ByteParsers.byte, n=4)

    source = b"\x01\x02\x03"
    actual = TstParser.test.parse(source)
    str(actual)
    assert isinstance(actual, Failure)
    assert "end of source" in repr(actual)


def test_calling_parse_with_a_reader():
    class TstParser(GeneralParsers):
        test = rep_n(ByteParsers.byte, n=4)

    source = b"\x01\x02\x03"
    from parsita.state import BytesReader

    reader = BytesReader(source)
    actual = TstParser.test.parse(reader)
    assert isinstance(actual, Failure)
    assert "end of source" in repr(actual)
