# -*- coding: utf-8 -*-
# © 20118 Eficent Business and IT Consulting Services S.L. (www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def get_move_lines_for_reconciliation(
            self, excluded_ids=None, str=False, offset=0, limit=None,
            additional_domain=None, overlook_partner=False):
        am_lines = super(AccountBankStatementLine, self).\
            get_move_lines_for_reconciliation(
            excluded_ids=excluded_ids, str=str, offset=offset, limit=limit,
            additional_domain=additional_domain,
            overlook_partner=overlook_partner)
        return am_lines.filtered(
            lambda line: not line.account_id.exclude_bank_reconcile)

    def _get_common_sql_query(
            self, overlook_partner=False, excluded_ids=None, split=False
    ):
        """
        The above function only handles searches for move lines, but we also
        want to apply the filtering already for the initial proposals
        """
        select_clause, from_clause, where_clause = super(
            AccountBankStatementLine, self
        )._get_common_sql_query(
            overlook_partner=overlook_partner, excluded_ids=excluded_ids,
            split=True,
        )
        where_clause += ' AND not acc.exclude_bank_reconcile'
        result = select_clause, from_clause, where_clause
        if not split:
            result = ''.join((select_clause, from_clause, where_clause))
        return result
