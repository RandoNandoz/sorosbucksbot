"""
Sorosbucks account.
"""
import time
import uuid

from transaction import Transaction


class Account:
    """
    Account for sorosbucks.
    """

    # noinspection PyDefaultArgument
    def __init__(self, name: str, account_number: uuid.UUID = None, balance: int = 1000,
                 transactions: list[Transaction] = [], overdraft_limit: int = -1000):
        """
        Initialize account.
        """
        self.nickname = name
        self._account_number = uuid.uuid4() if account_number is None else account_number
        self.balance = balance
        self.transactions = transactions
        self.overdraft_limit = overdraft_limit

    def get_account_number(self):
        return self._account_number

    def credit(self, amount: int):
        """
        Credit money to account.
        """
        #
        self.balance += amount

    def debit(self, amount: int):
        """
        Debit money from account.
        """
        if self.balance - amount >= self.overdraft_limit:
            self.balance -= amount
        else:
            raise ValueError('Insufficient funds')

    def transfer(self, recipient: 'Account', amount: int):
        """
        Transfer money from one account to another.
        """
        self.debit(amount)

        self.transactions.append(Transaction(recipient.get_account_number(), -amount, time.time(),
                                             f'Transfer of (debit) {amount} to {recipient._account_number}'))
        recipient.transactions.append(
            Transaction(recipient.get_account_number(), amount, time.time(),
                        f'Transfer of (credit) {amount} from {self._account_number}'))
        recipient.credit(amount)

    def __str__(self):
        return f'Account {self._account_number} with balance {self.balance}'

    def to_json(self):
        return {
            'nickname': self.nickname,
            'account_number': str(self._account_number),
            'balance': self.balance,
            'transactions': [t.to_json() for t in self.transactions],
            'overdraft_limit': self.overdraft_limit
        }

    @staticmethod
    def from_json(json_data: dict):
        return Account(json_data['nickname'], uuid.UUID(json_data['account_number']), json_data['balance'],
                       [Transaction.from_json(t) for t in json_data['transactions']], json_data['overdraft_limit'])
