from typing import List

from plenum.common.messages.batch_message import Batch
from plenum.common.messages.message import Message
from plenum.common.messages.message_factory import MessageFactory
from plenum.common.messages.message_handler import MessageHandler
from plenum.server.req_authenticator import ReqAuthenticator
from stp_core.common.log import getlogger
from stp_core.validators.message_length_validator import MessageLenValidator

logger = getlogger()


class BatchedMessageHandler(MessageHandler):
    SPLIT_STEPS_LIMIT = 8

    def __init__(self, authenticator: ReqAuthenticator, message_factory: MessageFactory):
        super().__init__(authenticator, message_factory)
        self.msg_len_val = MessageLenValidator(self.stp_config.MSG_LEN_LIMIT)

    # PUBLIC

    def process_output_msgs(self, msgs: List[Message]) -> List[bytes]:
        batches = self._makes_batches(msgs)
        return super().process_output_msgs(batches)

    # PROTECTED

    def _do_process_input_msg(self, msg: Message) -> List[Message]:
        if not isinstance(msg, Batch):
            return super()._do_process_input_msg(msg)

        result = []
        msg.validate()
        for m in msg.messages:
            result.extend(super()._do_process_input_msg(m))

        return result

    def _makes_batches(self, msgs: List[Message]) -> List[Message]:
        if not self._should_batch(msgs):
            return msgs

        logger.debug(
            "batching {} msgs into fewer transmissions".format(len(msgs)))
        logger.trace("    messages: {}".format(msgs))

        batches = self._split_messages_on_batches(list(msgs),
                                                  self._make_batch,
                                                  self._test_batch_len,
                                                  )
        msgs.clear()
        if batches:
            return batches
        else:
            logger.warning("cannot create batch(es) for {}"
                           .format(msgs))

    def _should_batch(self, msgs):
        return len(msgs) > 1

    def _make_batch(self, msgs: List[Message]):
        return Batch(msgs)

    def _test_batch_len(self, batch_len):
        return self.msg_len_val.is_len_less_than_limit(batch_len)

    @staticmethod
    def _split_messages_on_batches(msgs, make_batch_func, is_batch_len_under_limit,
                                   step_num=0):

        def split(rec_depth):
            len_2 = len(msgs) // 2
            left_batch = BatchedMessageHandler._split_messages_on_batches(msgs[:len_2], make_batch_func,
                                                                          is_batch_len_under_limit, rec_depth)
            right_batch = BatchedMessageHandler._split_messages_on_batches(msgs[len_2:], make_batch_func,
                                                                           is_batch_len_under_limit, rec_depth)
            return left_batch + right_batch if left_batch and right_batch else None

        if step_num > BatchedMessageHandler.SPLIT_STEPS_LIMIT:
            logger.warning('Too many split steps '
                           'were done {}. Batches were not created'.format(step_num))
            return None

        # precondition for case when total length is greater than limit
        # helps skip extra serialization step
        total_len = sum(len(m) for m in msgs)
        if not is_batch_len_under_limit(total_len):
            for m in msgs:
                if not is_batch_len_under_limit(len(m)):
                    logger.warning('The message {} is too long ({}). '
                                   'Batches were not created'.format(m, len(m)))
                    return
            step_num += 1
            return split(step_num)

        # make a batch and check its length
        batch = make_batch_func(msgs)
        if is_batch_len_under_limit(len(batch)):
            return [batch]  # success split
        else:
            if len(msgs) == 1:
                # a batch with this message greater than limit so split fails
                logger.warning('The message {} is less than limit '
                               'but the batch which contains only this '
                               'message has size {} which is greater than '
                               'limit'.format(msgs, len(batch)))
                return None
            step_num += 1
            return split(step_num)
