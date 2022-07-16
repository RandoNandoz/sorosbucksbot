"""
Sorosbucksbot for r/neoliberal.
"""

import os
import re
import time

import praw
import praw.models

from bank import Bank


def main():
    # track startup time so we don't reply to old comments
    startup_time = time.time()

    # initialize a bank, the datastructure for accounts
    bank = Bank()

    # Check if bank.json exists and is not empty, if both criteria are met, load the json file.
    if os.stat('bank.json').st_size > 0:
        bank = Bank('bank.json')

    # initialize a reddit instance, log into praw with env vars
    reddit = praw.Reddit(
        client_id=os.environ['REDDIT_CLIENT_ID'],
        client_secret=os.environ['REDDIT_CLIENT_SECRET'],
        user_agent=os.environ['REDDIT_USER_AGENT'],
        username=os.environ['REDDIT_USERNAME'],
        password=os.environ['REDDIT_PASSWORD']
    )

    # get r/nl as a subreddit object
    nl: praw.models.Subreddit = reddit.subreddit('neoliberal')

    # the ledger is the public list of transactions
    ledger: praw.models.Submission = reddit.submission(id='vzv97p')

    # leaderboard post is top 10 users
    leaderboard: praw.models.Submission = reddit.submission(id='vzxhre')

    # last check for leaderboard update
    last_check = time.time()

    # the stream of comments is the main loop
    for comment in nl.stream.comments():
        # if the comment is older than the startup time, ignore it, if we don't it is going to reply to comments after
        # a restart
        if comment.created_utc > startup_time:
            # if the comment's author does not exist or is the bot itself, ignore.
            if comment.author is None:
                continue
            if comment.author.name.lower() == 'sorosbucksbot':
                continue

            # help command
            if 'u/sorosbucksbot help' in comment.body.lower():
                # tell the user about the commands
                comment.reply(
                    'I am sorosbucksbot. I can facilitate transfers of a new DeFi project, sorosbucks, '
                    'exclusively available on r/neoliberal.\n\n'
                    'Type u/sorosbucksbot create to create a new account, you start off with 1000 sorosbucks, '
                    'and have a max overdraft of 1000 sorosbucks.\n\n'
                    'u/sorosbucksbot balance (optional: another user\'s username) - Check your/their balance.\n\n'
                    'u/sorosbucksbot transfer <amount> <user> - Transfer sorosbucks to another account.\n\n'
                    'u/sorosbucksbot issue <amount> <user> - Issue sorosbucks to another account (mod/dev only).\n\n'
                    'u/sorosbucksbot help - Show this message.\n\n'
                    'You can view the ledger at https://www.reddit.com/r/sorosbucksledger/comments/vzv97p/ledger/\n\n'
                    'My source code is available at: https://github.com/RandoNandoz/sorosbucksbot'
                )
                continue
            # create account command
            elif 'u/sorosbucksbot create' in comment.body.lower():
                # try to create an account
                try:
                    bank.create_account(comment.author.name.lower())
                    bank.save('bank.json')
                # if the account already exists, tell the user
                except ValueError:
                    comment.reply(f'You already have an account, '
                                  f'Wallet ID: {bank.get_account(comment.author.name.lower()).get_account_number()}')
                    continue
                # if the account was created, tell the user
                comment.reply(f'Account created for u/{comment.author.name.lower()}, '
                              f'Wallet ID: {bank.get_account(comment.author.name.lower()).get_account_number()}'
                              f', with balance 1000 and overdraft limit 1000. See the ledger at '
                              f'https://www.reddit.com/r/sorosbucksledger/comments/vzv97p/ledger/, '
                              f'and the leaderboard at '
                              f'https://www.reddit.com/r/sorosbucksledger/comments/vzxhre/leaderboard/'
                              )
                # if the account was created, update the ledger
                ledger.reply(f'Created account ID {bank.get_account(comment.author.name.lower()).get_account_number()},'
                             f' with balance 1000 and overdraft limit 1000')
            # balance command for other users
            elif 'u/sorosbucksbot balance u/' in comment.body.lower():
                # try to get the account of the user
                try:
                    account_to_check = bank.get_account(
                        comment.body.split('u/sorosbucksbot balance u/')[1].split(' ')[0])
                except ValueError:
                    # if the account does not exist, tell the user
                    comment.reply('That user does not have an account. Create an account with `u/sorosbucksbot create`.')
                    bank.save('bank.json')
                    continue
                # if the account exists, tell the user
                comment.reply(f'Balance: {account_to_check.balance}')
                continue
            # balance command for the user that asks the bot
            elif 'u/sorosbucksbot balance' in comment.body.lower():
                try:
                    # try to get the account of the user
                    account = bank.get_account(comment.author.name.lower())
                except ValueError:
                    # if the account does not exist, tell the user
                    comment.reply('You do not have an account. Create an account with `u/sorosbucksbot create`.')
                    continue
                # if the account exists, tell the user
                comment.reply(f'Balance: {account.balance}')
                continue

            # transfer command
            elif 'u/sorosbucksbot transfer' in comment.body.lower():
                try:
                    # try to get the account of the user
                    my_account = bank.get_account(comment.author.name.lower())
                except ValueError:
                    # if the account does not exist, tell the user
                    comment.reply('You do not have an account. Create an account with `u/sorosbucksbot create`.')
                    continue
                try:
                    # try to get the account of the transferee
                    amount = int(comment.body.split('u/sorosbucksbot transfer ')[1].split(' ')[0])
                    if amount <= 0:
                        raise ValueError
                except ValueError:
                    # if the amount is doesn't exist, tell the user
                    comment.reply('Invalid amount.')
                    bank.save('bank.json')
                    continue
                try:
                    # try to get the account of the transferee, but splice away the u/.
                    recipient = bank.get_account(
                        # I ❤️ regex
                        re.sub(r'.*/', '', comment.body.split('u/sorosbucksbot transfer ')[1]).lower())
                except ValueError:
                    # if the transferee does not exist, tell the user
                    comment.reply('Invalid recipient.')
                    bank.save('bank.json')
                    continue
                try:
                    # try the transfer
                    my_account.transfer(recipient, amount)
                    bank.save('bank.json')
                except ValueError:
                    # nsf alert
                    comment.reply(
                        f'Insufficient funds, you can at most transfer '
                        f'{my_account.balance + abs(my_account.overdraft_limit)} sorosbucks.')
                    bank.save('bank.json')
                    continue
                # if the transfer was successful, tell the user
                comment.reply(f'Transferred {amount} sorosbucks to wallet address {recipient.get_account_number()}\n\n'
                              f'View my ledger at https://www.reddit.com/r/sorosbucksledger/comments/vzv97p/ledger/,'
                              f' and view my leaderboard at '
                              f'https://www.reddit.com/r/sorosbucksledger/comments/vzxhre/leaderboard/')
                # update the ledger on sucess
                ledger.reply(
                    f'{my_account.get_account_number()} transferred '
                    f'{amount} to wallet address {recipient.get_account_number()}')

            # mod/dev only issue command
            elif 'u/sorosbucksbot issue' in comment.body.lower():
                # get all approved_users
                approved_users = [mod for mod in nl.moderator()]
                # dev is also approved too
                approved_users.append('HexagonOfVirtue')
                approved_users.append('qtnl')
                # if the user is trying to be sus and issue sorosbucks, but they aren't allowed to, tell them!
                if comment.author.name not in approved_users:
                    comment.reply('You must be a moderator to issue sorosbucks.')
                    bank.save('bank.json')
                    continue
                try:
                    # try to get the number of sorosbucks to issue
                    amount = int(comment.body.split('u/sorosbucksbot issue ')[1].split(' ')[0])
                except ValueError:
                    comment.reply('Invalid amount.')
                    bank.save('bank.json')
                    continue
                try:
                    # try to get the bank account of the user the issuer deems worthy of sorosbucks
                    recipient = bank.get_account(
                        re.sub(r'.*/', '', comment.body.split('u/sorosbucksbot issue ')[1]).lower())
                except ValueError:
                    comment.reply('Invalid recipient.')
                    bank.save('bank.json')
                    continue
                # credit account with sorosbucks if all is valid
                recipient.credit(amount)
                bank.save('bank.json')
                # update the ledger and confirm
                comment.reply(f'Issued {amount} sorosbucks to wallet address {recipient.get_account_number()}\n\n')
                ledger.reply(f'A moderator issued {amount} to wallet address {recipient.get_account_number()}')

        # save bank every 6 minutes and also update leaderboard.
        if time.time() - last_check > 360:
            last_check = time.time()
            bank.save('bank.json')
            top_users = bank.top_balances()
            try:
                leaderboard.edit(
                    f'**Leaderboard**\n\n'
                    f'1. {top_users[0].nickname}: Balance: {top_users[0].balance}\n\n'
                    f'2. {top_users[1].nickname}: Balance: {top_users[1].balance}\n\n'
                    f'3. {top_users[2].nickname}: Balance: {top_users[2].balance}\n\n'
                    f'4. {top_users[3].nickname}: Balance: {top_users[3].balance}\n\n'
                    f'5. {top_users[4].nickname}: Balance: {top_users[4].balance}\n\n'
                    f'6. {top_users[5].nickname}: Balance: {top_users[5].balance}\n\n'
                    f'7. {top_users[6].nickname}: Balance: {top_users[6].balance}\n\n'
                    f'8. {top_users[7].nickname}: Balance: {top_users[7].balance}\n\n'
                    f'9. {top_users[8].nickname}: Balance: {top_users[8].balance}\n\n'
                    f'10. {top_users[9].nickname}: Balance: {top_users[9].balance}\n\n'
                )
            except IndexError:
                leaderboard.edit(
                    f'**Leaderboard**\n\n'
                    f'Not enough users to generate board!'
                )
                print("Not enough users to generate board!")


if __name__ == '__main__':
    main()
