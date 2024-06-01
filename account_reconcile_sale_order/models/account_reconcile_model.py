# Copyright 2024 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import fields, models


class AccountReconcileModel(models.AbstractModel):
    _inherit = "account.reconcile.model"

    rule_type = fields.Selection(
        selection_add=[("sale_order_matching", "Rule to match sale orders")],
        ondelete={"sale_order_matching": "cascade"},
    )

    def _get_candidates(self, st_lines_with_partner, excluded_ids):
        if self.rule_type == "sale_order_matching":
            return self._get_candidates_sale_order(st_lines_with_partner, excluded_ids)
        else:
            return super()._get_candidates(st_lines_with_partner, excluded_ids)

    def _get_rule_result(
        self, st_line, candidates, aml_ids_to_exclude, reconciled_amls_ids, partner_map
    ):
        if self.rule_type == "sale_order_matching":
            return self._get_rule_result_sale_order(
                st_line,
                candidates,
                aml_ids_to_exclude,
                reconciled_amls_ids,
                partner_map,
            )
        else:
            return super()._get_rule_result(
                st_line,
                candidates,
                aml_ids_to_exclude,
                reconciled_amls_ids,
                partner_map,
            )

    def _get_candidates_sale_order(self, st_lines_with_partner, excluded_ids):
        """Return candidates for matching sale orders"""
        return {
            line.id: self.env["sale.order"].search(
                self.env[
                    "account.reconciliation.widget"
                ]._get_sale_orders_for_bank_statement_line_domain(
                    line.id, partner.id, amount=line.amount
                )
            )
            for line, partner in st_lines_with_partner
        }

    def _get_rule_result_sale_order(
        self, st_line, candidates, aml_ids_to_exclude, reconciled_amls_ids, partner_map
    ):
        return (
            {
                "model": self,
                "status": "sale_order_matching",
                "aml_ids": candidates,
                "write_off_vals": [
                    self.env[
                        "account.reconciliation.widget"
                    ]._reconciliation_proposition_from_sale_order(order)
                    for order in candidates
                ],
            },
            set(),
            set(),
        )
