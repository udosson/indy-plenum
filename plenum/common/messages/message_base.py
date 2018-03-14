from abc import ABCMeta, abstractmethod
from collections import OrderedDict, namedtuple
from ctypes.wintypes import MSG
from operator import itemgetter
from typing import Mapping, Iterable, List

from plenum.common.constants import MSG_TYPE, MSG_VERSION, PROTOCOL_VERSION, PLUGIN_FIELDS, MSG_DATA, MSG_FROM, MSG_SER, \
    MSG_SIGNATURE, MSG_PAYLOAD_DATA, MSG_PAYLOAD_PROTOCOL_VERSION, MSG_PAYLOAD_METADATA, MSG_PAYLOAD_PLUGIN_DATA
from plenum.common.messages.fields import FieldValidator, NonNegativeNumberField, AnyMapField, NonEmptyStringField, \
    SerializedValueField
from plenum.common.types import f


class MessageValidator():
    # the schema has to be an ordered iterable because the message class
    # can be create with positional arguments __init__(*args)

    schema = ()
    optional = False
    schema_is_strict = True

    def __init__(self, schema_is_strict=True):
        self.schema_is_strict = schema_is_strict

    def validate(self, dct, schema):
        self._validate_fields_with_schema(dct, schema)
        self._validate_message(dct)

    def _validate_fields_with_schema(self, dct, schema):
        if not isinstance(dct, dict):
            self._raise_invalid_type(dct)
        schema_dct = dict(schema)
        required_fields = filter(lambda x: not x[1].optional, schema)
        required_field_names = map(lambda x: x[0], required_fields)
        missed_required_fields = set(required_field_names) - set(dct)
        if missed_required_fields:
            self._raise_missed_fields(*missed_required_fields)
        for k, v in dct.items():
            if k not in schema_dct:
                if self.schema_is_strict:
                    self._raise_unknown_fields(k, v)
            else:
                validation_error = schema_dct[k].validate(v)
                if validation_error:
                    self._raise_invalid_fields(k, v, validation_error)

    def _validate_message(self, dct):
        return None

    def _raise_invalid_type(self, dct):
        raise TypeError("{} invalid type {}, dict expected"
                        .format(self.__error_msg_prefix, type(dct)))

    def _raise_missed_fields(self, *fields):
        raise TypeError("{} missed fields - {}"
                        .format(self.__error_msg_prefix,
                                ', '.join(map(str, fields))))

    def _raise_unknown_fields(self, field, value):
        raise TypeError("{} unknown field - "
                        "{}={}".format(self.__error_msg_prefix,
                                       field, value))

    def _raise_invalid_fields(self, field, value, reason):
        raise TypeError("{} {} "
                        "({}={})".format(self.__error_msg_prefix, reason,
                                         field, value))

    def _raise_invalid_message(self, reason):
        raise TypeError("{} {}".format(self.__error_msg_prefix, reason))

    @property
    def __error_msg_prefix(self):
        return 'validation error [{}]:'.format(self.__class__.__name__)

SchemaField = namedtuple("SchemaField", ["fld", "fldName", "fldType"])

class MessageBase(Mapping, metaclass=ABCMeta):


    @abstractmethod
    @property
    def schema(self) -> List[SchemaField]:
        pass

    def init(self, *args, **kwargs):
        assert not (args and kwargs), \
            '*args, **kwargs cannot be used together'

        argsLen = len(args or kwargs)
        assert argsLen <= len(self.schema), \
            "number of parameters should be less than or equal to " \
            "the number of fields in schema, but it was {}".format(argsLen)

        input_as_dict = kwargs if kwargs else self.__join_with_schema(args, self.schema)

        # TODO: support renaming of values in input dict without a need to rename fields in Message Class
        for fld, fldName, fldType in self.schema:
            self.fld = input_as_dict[fldName]
        # self._fields = OrderedDict(
        #     (name, input_as_dict[name])
        #     for name, _ in self.schema
        #     if name in input_as_dict)

    def __join_with_schema(self, args, schema):
        return dict(zip(map(itemgetter(1), schema), args))

    def __getattr__(self, item):
        return self._fields[item]

    def __getitem__(self, key):
        values = list(self._fields.values())
        if isinstance(key, slice):
            return values[key]
        if isinstance(key, int):
            return values[key]
        raise TypeError("Invalid argument type.")

    def as_dict(self):
        return self.__dict__

    @property
    def __dict__(self):
        """
        Return a dictionary form.
        """
        return self._fields

    @property
    def __name__(self):
        return self.typename + ":" + self.version

    def __iter__(self):
        return self._fields.values().__iter__()

    def __len__(self):
        return len(self._fields)

    def items(self):
        return self._fields.items()

    def keys(self):
        return self._fields.keys()

    def values(self):
        return self._fields.values()

    def __str__(self):
        return "{}-{}: {}".format(self.typename, self.version, dict(self.items()))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not issubclass(other.__class__, self.__class__):
            return False
        return self._asdict() == other._asdict()

    def __hash__(self):
        h = 1
        for index, value in enumerate(list(self.__iter__())):
            h = h * (index + 1) * (hash(value) + 1)
        return h

    def __dir__(self):
        return self.keys()

    def __contains__(self, key):
        return key in self._fields

