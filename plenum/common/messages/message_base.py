from abc import ABCMeta
from typing import Sequence

from plenum.common.messages.fields import FieldBase, IterableField
from plenum.common.tools import lazy_field


class MessageValidator():
    # the schema has to be an ordered iterable because the message class
    # can be create with positional arguments __init__(*args)

    schema_is_strict = True

    def validate(self):
        self._validate_fields_with_schema(self.attrs_as_dict)
        self._validate_message(self.attrs_as_dict)

    def _validate_fields_with_schema(self, dct):
        if not isinstance(dct, dict):
            self._raise_invalid_type(dct)
        schema_dct = self.validator_schema

        # required_fields = filter(lambda x: not x[1].optional, schema_dct)
        # required_field_names = map(lambda x: x[0], required_fields)
        required_field_names = [field_name
                                for field_name, validator in schema_dct.items()
                                if not validator.optional]
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

                # validate complex fields
                if isinstance(v, MessageBase):
                    v.validate()
                if isinstance(v, Sequence):
                    for _v in v:
                        if isinstance(_v, MessageBase):
                            _v.validate()

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


class InputField(object):

    def __call__(self, obj, name, validator, initial=None):
        return InputFieldAttribute(obj, name, validator, initial)

    def __init__(self):
        print("AAAA")

    def __get__(self, obj, objtype):
        print("EEEE")
        #return getattr(obj, self.name, self.value)
        return None
    #
    # def __set__(self, obj, value):
    #     print("FFFF")
    #     #setattr(obj, self.name, value)
    #     obj._attrs_by_names[self.name] = value

class InputFieldAttribute(object):

    def __init__(self, obj, name, validator, initial=None):
        obj.validator_schema[name] = validator
        obj._attrs_by_names[name] = initial
        # self.value = initial
        self.name = name
        # self.validator = validator
        print("DDD")

    def __get__(self, obj, objtype):
        print("EEEE")
        #return getattr(obj, self.name, self.value)
        return obj._attrs_by_names[self.name]
    def __set__(self, obj, value):
        print("FFFF")
        #setattr(obj, self.name, value)
        obj._attrs_by_names[self.name] = value


class MessageBase(MessageValidator, metaclass=ABCMeta):

    def __init__(self) -> None:
        self.validator_schema = {}
        self._fields = {}

    # @property
    # def validator_schema(self):
    #     return {
    #         name: validator
    #         for name, (attr_name, validator) in self._attrs_by_names.items()
    #     }

    @property
    def as_dict(self):
        return self._fields
        # {
        #     name: getattr(self, attr_name)
        #     for name, (attr_name, validator) in self._attrs_by_names.items()
        # }

    # @lazy_field
    # def _attrs_by_names(self):
    #     return {
    #         attr.name: (attr_name, attr.validator)
    #         for attr_name, attr in vars(type(self)).items()
    #         if isinstance(attr, InputField)
    #     }

    def init_from_dict(self, input_as_dict):
        for name, validator in self.validator_schema.items():
            if name not in input_as_dict:
                continue
            value = input_as_dict[name]
            if isinstance(validator, IterableField):
                value = self.__get_list_value(validator, value)
            elif isinstance(validator, MessageField):
                value = self.__get_msg_value(validator, value)
            setattr(self, name, value)

    def __get_msg_value(self, validator, input_as_dict):
        cls = validator.cls
        value = cls()
        value.init_from_dict(input_as_dict)
        return value

    def __get_list_value(self, validator: IterableField, input_as_list):
        inner_validator = validator.inner_field_type
        if not isinstance(inner_validator, MessageField):
            return input_as_list

        value = []
        for input_as_dict in input_as_list:
            value.append(self.__get_msg_value(inner_validator, input_as_dict))

        return value

    def __getattr__(self, name):
        if name == 'validator_schema':
            return super().__getattr__(name)
        if name in self.validator_schema:
            return self._fields[name]
        return super().__getattr__(name)

    def __setattr__(self, name, value):
        if name == 'validator_schema':
            super().__setattr__(name, value)
        elif name in self.validator_schema:
            self._fields[name] = value
        else:
            super().__setattr__(name, value)


class MessageField(FieldBase):
    _base_types = (MessageBase,)

    def __init__(self, cls,
                 **kwargs):
        super().__init__(**kwargs)
        self.cls = cls

    def _specific_validation(self, val):
        pass

# def input_field(attr_name, validator):
#     attr_name = attr_name
#     validator = validator
#
#     def wrapper(prop):
#
#         def wrapped(self):
#             if attr_name not in self.validator_schema:
#                 self.validator_schema[attr_name] = validator
#             return self._attrs_by_names.get(attr_name, None)
#
#         return wrapped
#
#     return wrapper

def input_field(msg: MessageBase, field: str, attr_name: str, validator, value=None):
    msg.validator_schema[attr_name] = validator
    msg._fields[attr_name] = field
    return value