from abc import ABCMeta
from typing import Sequence

from plenum.common.messages.fields import FieldBase, IterableField


class MessageValidator():
    schema_is_strict = True

    def validate_fields_with_schema(self, schema, attrs_as_dict):
        if not isinstance(attrs_as_dict, dict):
            self._raise_invalid_type(attrs_as_dict)

        # required_fields = filter(lambda x: not x[1].optional, schema_dct)
        # required_field_names = map(lambda x: x[0], required_fields)
        required_field_names = [field_name
                                for field_name, validator in schema.items()
                                if not validator.optional]
        missed_required_fields = set(required_field_names) - set(attrs_as_dict)

        if missed_required_fields:
            self._raise_missed_fields(*missed_required_fields)

        for k, v in attrs_as_dict.items():
            if k not in schema:
                if self.schema_is_strict:
                    self._raise_unknown_fields(k, v)
            else:
                validation_error = schema[k].validate(v)
                if validation_error:
                    self._raise_invalid_fields(k, v, validation_error)

                # validate complex fields
                if isinstance(v, MessageBase):
                    v.validate()
                if isinstance(v, Sequence):
                    for _v in v:
                        if isinstance(_v, MessageBase):
                            _v.validate()

    def validate_message(self, attrs_as_dict):
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


class MessageBase(MessageValidator, metaclass=ABCMeta):
    schema = ()

    @property
    def validator_schema(self):
        return {
            schema_item[1]: schema_item[2]
            for schema_item in self.schema
        }

    @property
    def _as_dict(self):
        return {
            schema_item[1]: getattr(self, schema_item[0])
            for schema_item in self.schema
        }

    def validate(self):
        attr_as_dict = self._as_dict
        self.validate_fields_with_schema(self.validator_schema, attr_as_dict)
        self.validate_message(attr_as_dict)

    def to_dict(self):
        res = {}
        for schema_item in self.schema:
            attr = getattr(self, schema_item[0])
            if isinstance(attr, MessageBase):
                attr = attr.to_dict()
            res[schema_item[1]] = attr
        return res

    def init_from_dict(self, input_as_dict):
        for field, attr_name, validator in self.schema:
            if attr_name not in input_as_dict:
                continue
            value = input_as_dict[attr_name]
            if isinstance(validator, IterableField):
                value = self.__get_list_value(validator, value)
            elif isinstance(validator, MessageField):
                value = self.__get_msg_value(validator, value)
            setattr(self, field, value)

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


class MessageField(FieldBase):
    _base_types = (MessageBase,)

    def __init__(self, cls,
                 **kwargs):
        super().__init__(**kwargs)
        self.cls = cls

    def _specific_validation(self, val):
        pass
