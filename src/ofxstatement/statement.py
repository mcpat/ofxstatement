"""Statement model"""

from datetime import datetime
import hashlib

try:
    from math import isclose
except:
    def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
        return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

TRANSACTION_TYPES = [
    "CREDIT",       # Generic credit
    "DEBIT",        # Generic debit
    "INT",          # Interest earned or paid
    "DIV",          # Dividend
    "FEE",          # FI fee
    "SRVCHG",       # Service charge
    "DEP",          # Deposit
    "ATM",          # ATM debit or credit
    "POS",          # Point of sale debit or credit
    "XFER",         # Transfer
    "CHECK",        # Check
    "PAYMENT",      # Electronic payment
    "CASH",         # Cash withdrawal
    "DIRECTDEP",    # Direct deposit
    "DIRECTDEBIT",  # Merchant initiated debit
    "REPEATPMT",    # Repeating payment/standing order
    "OTHER"         # Other
]

ACCOUNT_TYPE = [
    "CHECKING",     # Checking
    "SAVINGS",      # Savings
    "MONEYMRKT",    # Money Market
    "CREDITLINE",   # Line of credit
]


class Statement(object):
    """Statement object containing statement items"""
    lines = None

    currency = None
    bank_id = None
    account_id = None

    start_balance = None
    start_date = None

    end_balance = None
    end_date = None

    def __init__(self, bank_id=None, account_id=None, currency=None):
        self.lines = []
        self.bank_id = bank_id
        self.account_id = account_id
        self.currency = currency

    def assert_valid(self):
        """Ensure that fields have valid values
        """
        assert self.currency, "default currency missing"

        assert self.bank_id, "bank id missing"
        assert len(self.bank_id) <= 9, "bank id '%s' too long" % self.bank_id

        assert self.account_id, "account id missing"
        assert len(self.account_id) <= 22, \
            "account id '%s' too long" % self.acct_id

        assert self.start_date, "start date for transaction data missing"
        assert self.end_date, "end date for transaction data missing"
        assert self.end_balance, "(ledger) balance value missing"


class StatementLine(object):
    """Statement line data.

    All fields are initialized with some sample data so that field type may be
    determined by interested parties. Constructor will reinitialize them to
    None (by default)
    """
    id = ""
    # Date transaction was posted to account
    date = datetime.now()
    memo = ""

    # Amount of transaction
    amount = 0.0

    # additional fields
    payee = ""

    # Date user initiated transaction, if known
    date_user = ""

    # Date funds are available (value date)
    date_avail = ""

    # Check (or other reference) number
    check_no = ""

    # Reference number that uniquely identifies the transaction. Can be used in
    # addition to or instead of a check_no
    refnum = ""

    # Transaction type, must be one of TRANSACTION_TYPES
    trntype = "CHECK"

    # Optional BankAccount instance
    bank_account_to = None

    # Optional alternative currency
    currency = ""

    def __init__(self, id=None, date=None, memo=None, amount=None):
        self.id = id
        self.date = date
        self.memo = memo
        self.amount = amount

        self.date_user = None
        self.date_avail = None
        self.payee = None
        self.check_no = None
        self.refnum = None
        self.currency = None

    def __str__(self):
        return """
        ID: %s, date: %s, amount: %s, payee: %s
        memo: %s
        check no.: %s
        """ % (self.id, self.date, self.amount, self.payee, self.memo,
               self.check_no)

    def assert_valid(self):
        """Ensure that fields have valid values
        """
        assert self.trntype in TRANSACTION_TYPES, \
            "trntype must be one of %s" % TRANSACTION_TYPES

        assert self.date, "date transaction was posted missing"
        assert self.amount, "transaction amount missing"

        assert self.id, "transaction id missing"
        assert len(self.id) <= 255, "transaction id '%s' too long" % self.id

        if self.bank_account_to:
            self.bank_account_to.assert_valid()

        if self.payee:
            assert len(self.payee) <= 32, "payee '%s' too long" % self.payee

        if self.check_no:
            assert len(self.check_no) <= 12, \
                "check number '%s' too long" % self.check_no

        if self.refnum:
            assert len(self.refnum) <= 32, \
                "reference number '%s' too long" % self.refnum

        if self.currency:
            assert len(self.currency) != 3, \
                "invalid currency '%s'" % self.currency


class BankAccount(object):
    """Structure corresponding to BANKACCTTO and BANKACCTFROM elements from OFX

    Open Financial Exchange uses the Banking Account aggregate to identify an
    account at an FI. The aggregate contains enough information to uniquely
    identify an account for the purposes of statement.
    """

    # Routing and transit number
    bank_id = ""
    # Bank identifier for international banks
    branch_id = ""
    # Account number
    acct_id = ""
    # Type of account, must be one of ACCOUNT_TYPE
    acct_type = ""
    # Checksum for international banks
    acct_key = ""

    def __init__(self, bank_id, acct_id, acct_type="CHECKING", branch_id=None,
                 acct_key=None):
        self.bank_id = bank_id
        self.acct_id = acct_id
        self.acct_type = acct_type

        self.branch_id = branch_id
        self.acct_key = acct_key

    def assert_valid(self):
        assert self.bank_id, "bank id missing"
        assert len(self.bank_id) <= 9, "bank id '%s' too long" % self.bank_id

        assert self.acct_id, "account id missing"
        assert len(self.acct_id) <= 22, \
            "account id '%s' too long" % self.acct_id

        assert self.acct_type in ACCOUNT_TYPE, \
            "acct_type must be one of %s" % ACCOUNT_TYPE

        if self.acct_key:
            assert len(self.acct_key) <= 22, \
                "account key '%s' too long" % self.acct_key

        if self.branch_id:
            assert len(self.branch_id) <= 22, \
                "branch id '%s' too long" % self.branch_id


def generate_transaction_id(stmt_line):
    """Generate pseudo-unique id for given statement line.

    This function can be used in statement parsers when real transaction id is
    not available in source statement.
    """
    return str(abs(hash((stmt_line.date,
                         stmt_line.memo,
                         stmt_line.amount))))


def generate_stable_transaction_id(stmt_line):
    """Generate stable pseudo-unique id for given statement line.

    This function can be used in statement parsers when real transaction id is
    not available in source statement.

    This function differs from generate_transaction_id in that it generates
    ids which are reproducible during different runs on the same input.
    """
    if stmt_line.bank_account_to is None:
        values = (str(stmt_line.date),
                  stmt_line.memo,
                  str(stmt_line.amount))
    else:
        values = (str(stmt_line.date),
                  str(stmt_line.amount),
                  stmt_line.bank_account_to.bank_id,
                  stmt_line.bank_account_to.acct_id)

    md5 = hashlib.md5((",".join(values)).encode())
    result = str(abs(int(md5.hexdigest()[:16], 16)))
    return result


def recalculate_balance(stmt):
    """Recalculate statement starting and ending dates and balances.

    When starting balance is not available, it will be assumed to be 0.

    This function can be used in statement parsers when balance information is
    not available in source statement.
    """

    total_amount = sum(sl.amount for sl in stmt.lines)

    stmt.start_balance = stmt.start_balance or 0.0
    stmt.end_balance = stmt.start_balance + total_amount
    stmt.start_date = min(sl.date for sl in stmt.lines)
    stmt.end_date = max(sl.date for sl in stmt.lines)


def check_balance(stmt):
    """Utility function to check the correctness of the given balances.

    It sums over all transactions and compares the result plus starting balance
    with the end balance. If both values are close enough (equality check is
    not applicable for floating point numbers) it returns True. False otherwise
    """
    total_amount = sum(sl.amount for sl in stmt.lines)
    return isclose(stmt.start_balance + total_amount, stmt.end_balance)
