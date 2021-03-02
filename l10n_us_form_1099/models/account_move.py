# Copyright (C) 2021 Open Source Integrators
# Copyright (C) 2019 Brian McMaster
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """ If lines are already added and user change the Partner than \
            set Default 'is_1099' from newly selected Partner """
        result = super(AccountMove, self)._onchange_partner_id()
        self.invoice_line_ids.is_1099 = self.partner_id.is_1099
        self.invoice_line_ids.type_1099_id = self.partner_id.type_1099_id.id
        self.invoice_line_ids.box_1099_misc_id = self.partner_id.box_1099_misc_id.id
        return result


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    is_1099 = fields.Boolean("Is a 1099?")
    type_1099_id = fields.Many2one("type.1099", string="1099 Type")
    box_1099_misc_id = fields.Many2one("box.1099.misc", string="1099-MISC Box")
    legal_id_number = fields.Char(
        related="partner_id.legal_id_number", string="Legal ID"
    )
    allow_modify = fields.Boolean("Allow Modify Lines", compute="_compute_allow_fields")

    @api.depends("product_id")
    def _compute_allow_fields(self):
        """
        Make Allow Modify = True if selected product is Service else False
        """
        for record in self:
            if record.product_id.type == "service":
                record.allow_modify = True
            else:
                record.allow_modify = False

    @api.model
    def default_get(self, default_fields):
        # OVERRIDE
        # Update is_1099, type_1099_id and box_1099_misc_id from default partner
        values = super(AccountMoveLine, self).default_get(default_fields)
        if values.get("partner_id"):
            partner = self.env["res.partner"].browse(values.get("partner_id"))
            values.update(
                {
                    "is_1099": partner.is_1099,
                    "type_1099_id": partner.type_1099_id.id,
                    "box_1099_misc_id": partner.box_1099_misc_id.id,
                }
            )
        return values

    @api.onchange("is_1099", "type_1099_id")
    def onchange_is_1099(self):
        if not self.is_1099:
            self.type_1099_id = False
            self.box_1099_misc_id = False
        type_1099_id = self.env.ref("l10n_us_form_1099.1099_type_misc")
        if self.type_1099_id != type_1099_id:
            self.box_1099_misc_id = False
