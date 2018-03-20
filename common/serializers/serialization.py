from common.serializers.base58_serializer import Base58Serializer
from common.serializers.base64_serializer import Base64Serializer
from common.serializers.json_serializer import JsonSerializer
from common.serializers.msgpack_serializer import MsgPackSerializer

ledger_txn_serializer = MsgPackSerializer()
ledger_hash_serializer = MsgPackSerializer()
domain_state_serializer = JsonSerializer()
pool_state_serializer = JsonSerializer()
client_req_rep_store_serializer = JsonSerializer()
multi_sig_store_serializer = JsonSerializer()
state_roots_serializer = Base58Serializer()
proof_nodes_serializer = Base64Serializer()
multi_signature_value_serializer = MsgPackSerializer()
signing_serialization = MsgPackSerializer()

transport_serialization = MsgPackSerializer()

