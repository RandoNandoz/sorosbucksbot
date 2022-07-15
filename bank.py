"""
Datastructure for accounts and transactions.
"""

import json

import account


class Bank:
    # bank will store accounts in dictionary with name as key and account object as value
    def __init__(self, file_name: str = None):
        self._accounts: dict[str, account.Account] = {}
        # load accounts from file if filled in
        if file_name is not None:
            _raw_accounts = json.load(open(file_name))
            for a in _raw_accounts:
                self._accounts[a] = account.Account.from_json(json_data=_raw_accounts[a])

    # create account function
    def create_account(self, user: str):
        if user in self._accounts:
            raise ValueError('Account already exists')
        self._accounts[user] = account.Account(user)

    # query to see if account exists
    def account_query(self, user: str) -> bool:
        if user not in self._accounts:
            return False
        return True

    # get account by name
    def get_account(self, user: str):
        if user not in self._accounts:
            raise ValueError('Account does not exist')
        return self._accounts[user]

    # save to file function
    def save(self, file_name: str):
        s = {}
        for a in self._accounts:
            s[a] = self._accounts[a].to_json()
        json.dump(s, open(file_name, 'w'))

    # get all transactions from all accounts
    def get_all_transactions(self):
        transactions = []
        for a in self._accounts:
            transactions.append(self._accounts[a].transactions)
        return transactions

    # get richest folks
    def top_balances(self):
        top_accounts: list[account.Account] = []
        for a in self._accounts:
            top_accounts.append(self._accounts[a])
        top_accounts.sort(key=lambda x: x.balance, reverse=True)
        return top_accounts[:10]
