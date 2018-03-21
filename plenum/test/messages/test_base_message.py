from typing import Sequence, List

import pytest

from plenum.common.messages.fields import NonEmptyStringField, LimitedLengthStringField, NonNegativeNumberField, \
    IterableField
from plenum.common.messages.message_base import MessageBase, MessageField


class TestMessage(MessageBase):
    schema = (
        ("a", "aaa", NonNegativeNumberField()),
        ("b", "bbb", LimitedLengthStringField(max_length=10)),
        ("c", "ccc", NonNegativeNumberField(optional=True))
    )

    def __init__(self, a: int = None, b: str = None, c: int = None):
        self.a = a
        self.b = b
        self.c = c


class SubMessage1(MessageBase):
    schema = (
        ("f1", "f111", NonNegativeNumberField()),
        ("f2", "f222", NonEmptyStringField()),
    )

    def __init__(self, f1: int = None, f2: str = None):
        self.f1 = f1
        self.f2 = f2


class SubMessage2(MessageBase):
    schema = (
        ("f3", "f333", NonEmptyStringField()),
        ("f4", "f4", MessageField(cls=SubMessage1)),
    )

    def __init__(self, f3: str = None, f4: SubMessage1 = None):
        self.f3 = f3
        self.f4 = f4


class ComplexMessage(MessageBase):
    schema = (
        ("f5", "f5", NonEmptyStringField()),
        ("f6", "f666", MessageField(cls=SubMessage2)),
    )

    def __init__(self, f5: str = None, f6: SubMessage2 = None):
        self.f5 = f5
        self.f6 = f6


class ComplexMessageList(MessageBase):
    schema = (
        ("f5", "f5", NonEmptyStringField()),
        ("f6", "f666", IterableField(MessageField(cls=SubMessage2))),
    )

    def __init__(self, f5: str = None, f6: List[SubMessage2] = None):
        self.f5 = f5
        self.f6 = f6


@pytest.fixture(params=['from_dict', 'in_constructor'])
def test_msg_inited(request) -> TestMessage:
    if request.param == 'from_dict':
        msg = TestMessage()
        msg.init_from_dict({"aaa": 111, "bbb": "222"})
    else:
        msg = TestMessage(a=111, b="222")
    return msg


@pytest.fixture(params=['from_dict', 'in_constructor'])
def complex_msg_inited(request) -> ComplexMessage:
    if request.param == 'from_dict':
        msg = ComplexMessage()
        input = {
            "f5": "111",
            "f666": {
                "f333": "222",
                "f4": {
                    "f111": 333,
                    "f222": "444",
                }
            }
        }
        msg.init_from_dict(input)
    else:
        sub_msg1 = SubMessage1(f1=333, f2="444")
        sub_msg2 = SubMessage2(f3="222", f4=sub_msg1)
        msg = ComplexMessage(f5="111", f6=sub_msg2)
    return msg


@pytest.fixture(params=['from_dict', 'in_constructor'])
def complex_msg_list_inited(request) -> ComplexMessageList:
    if request.param == 'from_dict':
        msg = ComplexMessageList()
        input = {
            "f5": "111",
            "f666": [
                {
                    "f333": "222",
                    "f4": {
                        "f111": 333,
                        "f222": "444",
                    }
                },
                {
                    "f333": "333",
                    "f4": {
                        "f111": 444,
                        "f222": "555",
                    }
                },
            ]
        }
        msg.init_from_dict(input)
    else:
        sub_msg11 = SubMessage1(f1=333, f2="444")
        sub_msg21 = SubMessage2(f3="222", f4=sub_msg11)
        sub_msg12 = SubMessage1(f1=444, f2="555")
        sub_msg22 = SubMessage2(f3="333", f4=sub_msg12)
        msg = ComplexMessageList(f5="111", f6=[sub_msg21, sub_msg22])
    return msg


def test_instantiate_msg():
    assert TestMessage()
    assert ComplexMessage()
    assert ComplexMessageList()


def test_init_msg(test_msg_inited):
    assert test_msg_inited.a == 111
    assert test_msg_inited.b == "222"
    assert test_msg_inited.c is None


def test_validator_schema():
    msg = TestMessage()
    validator_schema = msg.validator_schema
    assert isinstance(validator_schema, dict)
    assert isinstance(validator_schema["aaa"], NonNegativeNumberField)
    assert isinstance(validator_schema["bbb"], LimitedLengthStringField)


def test_attrs_as_dict(test_msg_inited):
    attrs_as_dict = test_msg_inited.as_dict
    assert isinstance(attrs_as_dict, dict)
    assert attrs_as_dict["aaa"] == 111
    assert attrs_as_dict["bbb"] == "222"


def test_init_complex_msg(complex_msg_inited):
    assert complex_msg_inited.f5 == "111"

    f6 = complex_msg_inited.f6
    assert isinstance(f6, SubMessage2)
    assert f6.f3 == "222"

    f4 = f6.f4
    assert isinstance(f4, SubMessage1)
    assert f4.f1 == 333
    assert f4.f2 == "444"


def test_init_complex_list_msg(complex_msg_list_inited):
    msg = complex_msg_list_inited
    assert msg.f5 == "111"

    f6 = msg.f6
    assert isinstance(f6, List)
    assert len(f6) == 2

    f6_0 = f6[0]
    f6_1 = f6[1]
    assert isinstance(f6_0, SubMessage2)
    assert isinstance(f6_1, SubMessage2)

    assert f6_0.f3 == "222"
    assert f6_1.f3 == "333"

    f4_0 = f6_0.f4
    assert isinstance(f4_0, SubMessage1)
    assert f4_0.f1 == 333
    assert f4_0.f2 == "444"

    f4_1 = f6_1.f4
    assert isinstance(f4_0, SubMessage1)
    assert f4_1.f1 == 444
    assert f4_1.f2 == "555"


def test_validate_by_schema(test_msg_inited):
    msg = test_msg_inited
    msg.validate()

    msg.a = -5
    with pytest.raises(TypeError) as ex_info:
        msg.validate()
    assert ex_info.match('negative value')

    msg.init_from_dict({"aaa": 10, "bbb": 10})
    with pytest.raises(TypeError) as ex_info:
        msg.validate()
    assert ex_info.match('expected types')


def test_validate_complex_by_schema(complex_msg_inited):
    msg = complex_msg_inited
    msg.validate()

    msg.f6.f4.f1 = -5
    with pytest.raises(TypeError) as ex_info:
        msg.validate()
    assert ex_info.match('negative value')

    msg.f6.f4.f1 = 5
    msg.f6.f3 = 1111
    with pytest.raises(TypeError) as ex_info:
        msg.validate()
    assert ex_info.match('expected types')


def test_validate_complex_list_by_schema(complex_msg_list_inited):
    msg = complex_msg_list_inited
    msg.validate()

    msg.f6[0].f4.f1 = -5
    with pytest.raises(TypeError) as ex_info:
        msg.validate()
    assert ex_info.match('negative value')

    msg.f6[0].f4.f1 = 5
    msg.f6[1].f4.f1 = -5
    with pytest.raises(TypeError) as ex_info:
        msg.validate()
    assert ex_info.match('negative value')

    msg.f6[1].f4.f1 = 5
    msg.f6[0].f3 = 1111
    with pytest.raises(TypeError) as ex_info:
        msg.validate()
    assert ex_info.match('expected types')

    msg.f6[0].f3 = "1111"
    msg.f6[1].f3 = 1111
    with pytest.raises(TypeError) as ex_info:
        msg.validate()
    assert ex_info.match('expected types')
