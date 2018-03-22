import sys
from importlib import import_module

from plenum.common.exceptions import MissingMsgType
from plenum.common.messages.constants.message_constants import MSG_TYPE, MSG_VERSION
from plenum.common.messages.message import Message
from plenum.common.messages.signed_message import SignedMessage


class MessageFactory:
    def __init__(self, class_module_names):
        for class_module_name in class_module_names:
            classes_module = self.__load_module_by_name(class_module_name)
            self.__classes = self.__get_message_classes(classes_module)
        assert len(self.__classes) > 0, "at least one message class loaded"

    @classmethod
    def __load_module_by_name(cls, module_name):
        the_module = cls.__get_module_by_name(module_name)
        if the_module is not None:
            return the_module

        import_module(module_name)  # can raise ImportError
        the_module = cls.__get_module_by_name(module_name)
        return the_module

    @staticmethod
    def __get_module_by_name(module_name):
        return sys.modules.get(module_name, None)

    @classmethod
    def __get_message_classes(cls, classes_module):
        classes = {}
        for x in dir(classes_module):
            obj = getattr(classes_module, x)
            doesnt_fit_reason = cls.__check_obj_fits(obj)
            if doesnt_fit_reason is None:
                classes.update({(obj.typename, obj.version): obj})
        return classes

    @staticmethod
    def __check_obj_fits(obj):
        print(obj)
        if not getattr(obj, "typename", None):
            return "must have a non empty 'typename'"
        if getattr(obj, "version", None) is None:
            return "must have a non empty 'version'"
        if getattr(obj, "need_signature", None) is True:
            return "use a SignedMessage wrapper instead"
        # has to be the last because of: 'str' week ref error
        if not issubclass(obj, Message) and not issubclass(obj, SignedMessage):
            return "must be a subclass of 'Message'"

    def get_instance(self, **message_raw) -> Message:
        message_type = message_raw.get(MSG_TYPE, None)
        message_version = message_raw.get(MSG_VERSION, 0)

        if message_type is None:
            raise MissingMsgType

        cls = self.get_type(message_type, message_version)
        return cls()

    def get_type(self, message_type, message_version):
        message_cls = self.__classes.get((message_type, message_version), None)
        if message_cls is None:
            raise MissingMsgType(message_type)
        return message_cls

    def set_message_class(self, message_class):
        doesnt_fit_reason = self.__check_obj_fits(message_class)
        assert not doesnt_fit_reason, doesnt_fit_reason
        self.__classes.update({(message_class.typename, message_class.version): message_class})


class NodeMessageFactory(MessageFactory):
    def __init__(self):
        super().__init__(['plenum.common.messages.node_messages'])


node_message_factory = NodeMessageFactory()
