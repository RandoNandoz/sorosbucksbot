"""
Transaction class for ledger
"""
import uuid


class Transaction:
    # transactions have recipient wallet addresses (in uuid), amounts, time (unix timesamp), and description
    def __init__(self, recipient: uuid.UUID, amount: int, timestamp: float, memo: str):
        self._timestamp = timestamp
        self._recipient = recipient
        self._amount = amount
        self._transaction_id = uuid.uuid4()
        self._memo = memo if memo else f'{amount} to {recipient}'

    def __str__(self):
        return f'{self._transaction_id}: Time: {self._timestamp} Memo: {self._memo} Amount: {self._amount} Recipient: {str(self._recipient)}'

    def get_transaction_id(self):
        return self._transaction_id

    # dump transaction to json
    def to_json(self):
        return {
            'timestamp': self._timestamp,
            'recipient': str(self._recipient),
            'amount': self._amount,
            'memo': self._memo,
            'transaction_id': str(self._transaction_id)
        }

    # no databases here, just json. turns dict from json read into a Transaction object
    @staticmethod
    def from_json(json_data: dict):
        return Transaction(uuid.UUID(json_data['recipient']), json_data['amount'], json_data['timestamp'],
                           json_data['memo'])
