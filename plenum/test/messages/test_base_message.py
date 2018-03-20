from typing import Sequence

import pytest

from plenum.common.messages.fields import NonEmptyStringField, LimitedLengthStringField, NonNegativeNumberField, \
    IterableField
from plenum.common.messages.message_base import MessageBase, InputField, MessageField, input_field


class TestMessage(MessageBase):

    def __init__(self) -> None:
        super().__init__()
        self.a = input_field(self, "aaa", NonNegativeNumberField())
        self.b = input_field(self, "bbb", LimitedLengthStringField(max_length=10))
        self.c = input_field(self, "bbb", NonNegativeNumberField(optional=True))


# class SubMessage1(MessageBase):
#     f1 = InputField("f111", NonNegativeNumberField())
#     f2 = InputField("f222", NonEmptyStringField())
#
#
# class SubMessage2(MessageBase):
#     f3 = InputField("f333", NonEmptyStringField())
#     f4 = InputField("f4", MessageField(cls=SubMessage1))
#
#
# class ComplexMessage(MessageBase):
#     f5 = InputField("f5", NonEmptyStringField())
#     f6 = InputField("f666", MessageField(cls=SubMessage2))
#
#
# class ComplexMessageList(MessageBase):
#     f5 = InputField("f5", NonEmptyStringField())
#     f6 = InputField("f6", IterableField(MessageField(cls=SubMessage2)))


@pytest.fixture()
def test_msg_inited():
    msg = TestMessage()
    msg.init_from_dict({"aaa": 111, "bbb": "222"})
    return msg


@pytest.fixture()
def complex_msg_inited():
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
    return msg


@pytest.fixture()
def complex_msg_list_inited():
    msg = ComplexMessageList()
    input = {
        "f5": "111",
        "f6": [
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
    return msg


def test_instantiate_msg():
    assert TestMessage()
    #assert ComplexMessage()
    #assert ComplexMessageList()


def test_init_msg_from_dict(test_msg_inited):
    assert test_msg_inited.a == 111
    assert test_msg_inited.b == "222"
    assert test_msg_inited.c is None


def test_validator_schema(test_msg_inited):
    validator_schema = test_msg_inited.validator_schema
    assert isinstance(validator_schema, dict)
    assert isinstance(validator_schema["aaa"], NonNegativeNumberField)
    assert isinstance(validator_schema["bbb"], LimitedLengthStringField)


def test_attrs_as_dict(test_msg_inited):
    validator_schema = test_msg_inited.attrs_as_dict
    assert isinstance(validator_schema, dict)
    assert validator_schema["aaa"] == 111
    assert validator_schema["bbb"] == "222"


def test_init_complex_msg_from_dict(complex_msg_inited):
    assert complex_msg_inited.f5 == "111"

    f6 = complex_msg_inited.f6
    assert isinstance(f6, SubMessage2)
    assert f6.f3 == "222"

    f4 = f6.f4
    assert isinstance(f4, SubMessage1)
    assert f4.f1 == 333
    assert f4.f2 == "444"


def test_init_complex_list_msg_from_dict(complex_msg_list_inited):
    msg = complex_msg_list_inited
    assert msg.f5 == "111"

    f6 = msg.f6
    assert isinstance(f6, Sequence)
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

    msg.init_from_dict({"aaa": -5, "bbb": "222"})
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
