import csv
import re

from datetime import datetime
from ofxstatement.statement import Statement, StatementLine


IBAN_PATTERN = re.compile("^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$")
IBAN_FORMATTINGS = {
    "AT": {"bank_id": (4, 9), "acct_id": (9, 20)},
    "BE": {"bank_id": (4, 7), "acct_id": (7, 14), "acct_key": (14, 16)},
    "CH": {"bank_id": (4, 9), "acct_id": (9, 21)},
    "DE": {"bank_id": (4, 12), "acct_id": (12, 22)},
    "DK": {"bank_id": (4, 8), "acct_id": (8, 17), "acct_key": (17, 18)},
    "FR": {"bank_id": (4, 9), "branch_id": (9, 14), "acct_id": (14, 25),
           "acct_key": (25, 27)},
    "GB": {"bank_id": (4, 8), "branch_id": (8, 14), "acct_id": (14, 22)},
    "IT": {"acct_key": (4, 5), "bank_id": (5, 10), "branch_id": (10, 15),
           "acct_id": (15, 27)},
}


class StatementParser(object):
    """Abstract statement parser.

    Defines interface for all parser implementation
    """

    date_format = "%Y-%m-%d"
    cur_record = 0

    def parse(self):
        """Read and parse statement

        Return Statement object

        May raise exceptions.ParseException on malformed input.
        """
        reader = self.split_records()
        for line in reader:
            self.cur_record += 1
            if not line:
                continue
            stmt_line = self.parse_record(line)
            if stmt_line:
                stmt_line.assert_valid()
                self.statement.lines.append(stmt_line)
        return self.statement

    def split_records(self):
        """Return iterable object consisting of a line per transaction
        """
        raise NotImplementedError

    def parse_record(self, line):
        """Parse given transaction line and return StatementLine object
        """
        raise NotImplementedError

    def parse_iban(self, iban):
        """Splits the IBAN into its parts.

        The result depends on the country that is also encoded in the IBAN.
        You can directly feed the map returned by this function as keyword
        arguments to the constructor of the BankAccount class!
        """

        # first remove spaces (if present)
        iban = iban.replace(" ", "")

        # check if it is really an IBAN
        m = IBAN_PATTERN.match(iban)
        result = dict()

        # now separate everything
        if m is not None:
            f = IBAN_FORMATTINGS[iban[:2]]
            for name, (start, end) in f.items():
                result[name] = iban[start:end].lstrip("0")

        return result

    def parse_value(self, value, field):
        tp = type(getattr(StatementLine, field))
        if tp == datetime:
            return self.parse_datetime(value)
        elif tp == float:
            return self.parse_float(value)
        else:
            return value

    def parse_datetime(self, value):
        return datetime.strptime(value, self.date_format)

    def parse_float(self, value):
        return float(value)


class CsvStatementParser(StatementParser):
    """Generic csv statement parser"""

    statement = None
    fin = None  # file input stream

    # 0-based csv column mapping to StatementLine field
    mappings = {}

    def __init__(self, fin):
        self.statement = Statement()
        self.fin = fin

    def split_records(self):
        return csv.reader(self.fin)

    def parse_record(self, line):
        stmt_line = StatementLine()
        for field, col in self.mappings.items():
            if col >= len(line):
                raise ValueError("Cannot find column %s in line of %s items "
                                 % (col, len(line)))
            rawvalue = line[col]
            value = self.parse_value(rawvalue, field)
            setattr(stmt_line, field, value)
        return stmt_line
