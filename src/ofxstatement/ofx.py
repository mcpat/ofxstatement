from datetime import datetime
from xml.etree import ElementTree as etree
from ofxstatement.configuration import APP_NAME, APP_VERSION


class OfxWriter(object):
    statement = None
    tb = None
    genTime = None

    def __init__(self, statement):
        self.statement = statement
        self.genTime = datetime.now()

    def toxml(self):
        self.tb = etree.TreeBuilder()
        et = self.buildDocument()
        encoded = etree.tostring(et.getroot(), "utf-8")
        encoded = str(encoded, "utf-8")
        header = ("<!-- \n"
                  "OFXHEADER:160\n"
                  "DATA:OFXSGML\n"
                  "VERSION:106\n"
                  "SECURITY:NONE\n"
                  "ENCODING:UTF-8\n"
                  "CHARSET:NONE\n"
                  "COMPRESSION:NONE\n"
                  "OLDFILEUID:NONE\n"
                  "NEWFILEUID:NONE\n"
                  "-->\n\n")

        return header + encoded

    def buildDocument(self):
        tb = self.tb
        tb.start("OFX", {})

        self.buildSignon()

        self.buildTransactionList()

        tb.end("OFX")
        return etree.ElementTree(tb.close())

    def buildSignon(self):
        tb = self.tb
        tb.start("SIGNONMSGSRSV1", {})
        tb.start("SONRS", {})
        tb.start("STATUS", {})
        self.buildText("CODE", "0", False)
        self.buildText("SEVERITY", "INFO", False)
        self.buildText("MESSAGE", "Created by %s (%s)" % (APP_NAME,
                                                          APP_VERSION))
        tb.end("STATUS")

        self.buildDateTime("DTSERVER", self.genTime, False)
        self.buildText("LANGUAGE", "ENG", False)

        tb.end("SONRS")
        tb.end("SIGNONMSGSRSV1")

    def buildTransactionList(self):
        tb = self.tb
        tb.start("BANKMSGSRSV1", {})
        tb.start("STMTTRNRS", {})

        self.buildText("TRNUID", "0")
        tb.start("STATUS", {})
        self.buildText("CODE", "0", False)
        self.buildText("SEVERITY", "INFO", False)
        tb.end("STATUS")

        tb.start("STMTRS", {})
        self.buildText("CURDEF", self.statement.currency)
        tb.start("BANKACCTFROM", {})
        self.buildText("BANKID", self.statement.bank_id, False)
        self.buildText("ACCTID", self.statement.account_id, False)
        self.buildText("ACCTTYPE", "CHECKING", False)
        tb.end("BANKACCTFROM")

        tb.start("BANKTRANLIST", {})
        self.buildDate("DTSTART", self.statement.start_date, False)
        self.buildDate("DTEND", self.statement.end_date, False)

        for line in self.statement.lines:
            self.buildTransaction(line)

        tb.end("BANKTRANLIST")

        tb.start("LEDGERBAL", {})
        self.buildAmount("BALAMT", self.statement.end_balance, False)
        self.buildDateTime("DTASOF", self.statement.end_date, False)
        tb.end("LEDGERBAL")

        tb.end("STMTRS")
        tb.end("STMTTRNRS")
        tb.end("BANKMSGSRSV1")

    def buildTransaction(self, line):
        tb = self.tb
        tb.start("STMTTRN", {})

        self.buildText("TRNTYPE", line.trntype, False)
        self.buildDate("DTPOSTED", line.date, False)
        self.buildDate("DTUSER", line.date_user)
        self.buildDate("DTAVAIL", line.date_avail)
        self.buildAmount("TRNAMT", line.amount, False)
        self.buildText("FITID", line.id, False)
        self.buildText("CHECKNUM", line.check_no)
        self.buildText("NAME", line.payee)
        self.buildText("MEMO", line.memo)
        self.buildText("REFNUM", line.refnum)
        self.buildText("CURRENCY", line.currency)
        if line.bank_account_to:
            tb.start("BANKACCTTO", {})
            self.buildBankAccount(line.bank_account_to)
            tb.end("BANKACCTTO")

        tb.end("STMTTRN")

    def buildBankAccount(self, account):
        self.buildText("BANKID", account.bank_id, False)
        self.buildText("BRANCHID", account.branch_id)
        self.buildText("ACCTID", account.acct_id, False)
        self.buildText("ACCTTYPE", account.acct_type, False)
        self.buildText("ACCTKEY", account.acct_key)

    def buildText(self, tag, text, optional=True):
        if not text:
            if optional:
                return
            # missing mandatory element
            raise ValueError("missing value for '%s'" % tag)

        self.tb.start(tag, {})
        self.tb.data(text or "")
        self.tb.end(tag)

    def buildDate(self, tag, dt, optional=True):
        if dt is None:
            self.buildText(tag, "", optional)
        else:
            self.buildText(tag, dt.strftime("%Y%m%d"))

    def buildDateTime(self, tag, dt, optional=True):
        if dt is None:
            self.buildText(tag, "", optional)
        else:
            self.buildText(tag, dt.strftime("%Y%m%d%H%M%S"))

    def buildAmount(self, tag, amount, optional=True):
        if amount is None:
            self.buildText(tag, "", optional)
        else:
            self.buildText(tag, "%.2f" % amount)
