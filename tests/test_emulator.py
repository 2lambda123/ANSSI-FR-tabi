import contextlib
import json

from tabi.emulator import detect_conflicts


@contextlib.contextmanager
def dict_opener(line):
    yield [json.dumps(line)]


def test_detect_conflicts_boundary_1():
    """Check if conflicts detection fails on empty file list"""
    try:
        conflicts = detect_conflicts("collector", [])
        conflicts.next()
        raise Exception("Should raise an exception on empty file list")
    except ValueError as error:
        assert error.message == "no bviews were loaded"


def test_detect_conflicts_boundary_2():
    """Check if conflicts detection fails on a file with partial data"""
    try:
        conflicts = detect_conflicts("collector", [{"type": "table_dump_v2"}], opener=dict_opener)
        conflicts.next()
        raise Exception("There shouldn't be any conflict to report")
    except StopIteration:
        pass


def test_detect_conflicts_rib_update():
    """Check if conflicts detection works for a conflict between rib and update files"""
    rib = {
        "entries": [{
            "peer_ip": "11:33:55:77",
            "peer_as": 99999.0,
            "originated_timestamp": 0.0,
            "as_path": "22 333 4444 55555"
        }],
        "type": "table_dump_v2",
        "timestamp": 1451601234.0,
        "prefix": "1.2.3.0/24"
    }
    update = {
        "type": "update",
        "timestamp": 1451606698.0,
        "peer_as": 11111.0,
        "peer_ip": "22.44.66.88",
        "as_path": "1111 2222 3333",
        "announce": ["1.2.3.0/25"],
        "withdraw": []
    }
    conflicts = detect_conflicts("collector", [rib, update], opener=dict_opener)
    conflict = conflicts.next()
    expected = {
        'timestamp': 1451606698.0,
        'collector': 'collector',
        'peer_as': 11111,
        'peer_ip': "22.44.66.88",
        'announce': {
            'type': 'U',
            'prefix': '1.2.3.0/25',
            'asn': 3333,
            'as_path': '1111 2222 3333'
        },
        'conflict_with': {
            'asn': 55555,
            'prefix': '1.2.3.0/24'
        },
        'asn': 55555
    }
    assert conflict == expected


def test_detect_conflicts_rib_only():
    """Check if conflicts detection works for a conflict within rib file"""
    rib1 = {
        "entries": [{
            "peer_ip": "11.33.55.77",
            "peer_as": 66666.0,
            "originated_timestamp": 1451606699.0,
            "as_path": "22 333 4444 66666"
        }],
        "type": "table_dump_v2",
        "timestamp": 1451606699.0,
        "prefix": "1.2.3.0/24"
    }
    rib2 = {
        "entries": [{
            "peer_ip": "22.44.66.88",
            "peer_as": 99999.0,
            "originated_timestamp": 1451605511.0,
            "as_path": "22 333 4444 55555"
        }],
        "type": "table_dump_v2",
        "timestamp": 1451605511.0,
        "prefix": "1.2.3.0/24"
    }
    conflicts = detect_conflicts("collector", [rib1, rib2], opener=dict_opener)
    conflict = conflicts.next()
    expected = {
        'timestamp': 1451606699.0,
        'collector': 'collector',
        'peer_as': 66666,
        'peer_ip': "11.33.55.77",
        'announce': {
            'type': 'F',
            'prefix': '1.2.3.0/24',
            'asn': 66666,
            'as_path': '22 333 4444 66666'
        },
        'conflict_with': {
            'asn': 55555,
            'prefix': '1.2.3.0/24'
        },
        'asn': 55555
    }
    assert conflict == expected
