# Copyright 2024 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def process_reconciliation(
        self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None
    ):
        """
        Invoice selected sale orders and use resulting move lines
        """
        new_aml_dicts2 = []
        counterpart_aml_dicts = (counterpart_aml_dicts or [])[:]
        for new_aml_dict in new_aml_dicts or []:
            sale_order_id = new_aml_dict.get("sale_order_id")
            if sale_order_id:
                order = self.env["sale.order"].browse(sale_order_id)
                self._process_reconciliation_sale_order_invoice(order)
                counterpart_aml_dicts += (
                    self._process_reconciliation_sale_order_counterparts(order)
                )
            else:
                new_aml_dicts2.append(new_aml_dict)

        return super().process_reconciliation(
            counterpart_aml_dicts=counterpart_aml_dicts,
            payment_aml_rec=payment_aml_rec,
            new_aml_dicts=new_aml_dicts2,
        )

    def _process_reconciliation_sale_order_invoice(self, order):
        """
        Invoice selected sale orders and post the invoices
        """
        if order.state in ("draft", "sent"):
            order.action_confirm()
        order.flush()
        wizard = (
            self.env["sale.advance.payment.inv"]
            .with_context(
                active_ids=order.ids,
                active_id=order.ids[:1],
                active_model=order._name,
            )
            .with_company(order.company_id)
            .with_user(order.user_id)
            .create(
                {
                    "advance_payment_method": "delivered",
                }
            )
        )
        wizard.create_invoices()
        order.flush()
        order.invoice_ids.filtered(lambda x: x.state == "draft").action_post()

    def _process_reconciliation_sale_order_counterparts(self, order):
        """
        Return counterpart aml dicts for sale order
        """
        import logging

        logger = logging.getLogger("hbrunn debug")
        logger.info(
            "order %s, untaxed %s, tax %s, total %s, json %s",
            order.name,
            order.amount_untaxed,
            order.amount_tax,
            order.amount_total,
            order.tax_totals_json,
        )
        for invoice in order.mapped("invoice_ids"):
            logger.info(
                "invoice %s, untaxed %s, tax %s, total %s, json %s",
                invoice.name,
                invoice.amount_untaxed,
                invoice.amount_tax,
                invoice.amount_total,
                invoice.tax_totals_json,
            )
        for line in order.order_line:
            logger.info(
                "order line %s, untaxed %s, tax %s, total %s",
                line.name,
                line.price_subtotal,
                line.price_tax,
                line.price_total,
            )
            logger.info("   invoice line %s", line.invoice_lines)
        for line in order.mapped("invoice_ids.line_ids"):
            logger.info(
                "move line %s(%d), type %s, credit %s, debit %s, balance %s",
                line.name,
                line.id,
                line.account_id.user_type_id.type,
                line.credit,
                line.debit,
                line.balance,
            )
        self.env.clear()
        for line in order.mapped("invoice_ids.line_ids"):
            logger.info(
                "move line %s(%d), type %s, credit %s, debit %s, balance %s",
                line.name,
                line.id,
                line.account_id.user_type_id.type,
                line.credit,
                line.debit,
                line.balance,
            )
        return [
            {
                "name": line.name,
                "move_line": line,
                "debit": line.credit,
                "credit": line.debit,
                "analytic_tag_ids": [(6, 0, line.analytic_tag_ids.ids)],
            }
            for line in order.mapped("invoice_ids.line_ids")
            if line.account_id.user_type_id.type == "receivable"
        ]
