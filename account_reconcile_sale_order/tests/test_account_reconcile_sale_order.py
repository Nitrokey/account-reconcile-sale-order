# Copyright 2024 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo.tests import tagged

from odoo.addons.account.tests.common import TestAccountReconciliationCommon


@tagged("post_install", "-at_install")
class TestAccountReconcileSaleOrder(TestAccountReconciliationCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        partner = cls.env.ref("base.res_partner_12")
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Order line",
                            "price_unit": 4242,
                            "product_id": cls.env.ref("product.consu_delivery_01").id,
                        },
                    )
                ],
            }
        )
        cls.sale_order.action_confirm()
        cls.bank_statement = cls.env["account.bank.statement"].create(
            {
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "bank payment",
                            "amount": 4242,
                            "payment_ref": "/",
                            "partner_id": partner.id,
                        },
                    )
                ],
                "journal_id": cls.bank_journal_euro.id,
            }
        )

    def test_reconcile_sale_order(self):
        model = self.env.ref("account_reconcile_sale_order.reconcile_model_sale_order")
        self.assertEqual(self.sale_order.invoice_status, "to invoice")
        rule_result = model.sudo()._apply_rules(self.bank_statement.line_ids)
        line_result = rule_result[self.bank_statement.line_ids.id]
        self.assertEqual(line_result["status"], "sale_order_matching")
        self.bank_statement.line_ids.process_reconciliation(
            new_aml_dicts=line_result["write_off_vals"],
        )
        self.assertEqual(self.sale_order.invoice_status, "invoiced")
