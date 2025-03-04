# Copyright 2020 Lokavaluto ()
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class PortalPrivateRegistration(CustomerPortal):
    _PRIVATE_REGISTRATION_FIELDS = [
        "firstname",
        "lastname",
        "street",
        "street2",
        "city",
        "zipcode",
        "country_id",
        "team_id",
        "phone",
        "mobile",
        "title",
    ]

    # Variable to update to add other fields in child classes
    _EXTRA_FIELDS = []

    def _membership_get_page_view_values(self, partner, access_token, **kwargs):
        values = {
            "page_name": "portal_private_registration",
            "partner": partner,
        }
        return self._get_page_view_values(
            partner,
            access_token,
            values,
            "my_private_registration_history",
            False,
            **kwargs
        )

    def get_private_membership_product(self):
        product_obj = request.env["product.template"]
        product = product_obj.sudo().get_private_membership_product(
            request.env.user.partner_id.company_id.id
        )
        return product

    def _get_selected_team_id(self, partner):
        if len(request.env['res.company'].sudo().search([])) > 1:
            return request.env["crm.team"].sudo().search([("local_group", "=", True), ("company_id", "=", partner.company_id.id)])
        else:
            return request.env["crm.team"].sudo().search([("local_group", "=", True)])

    @http.route(
        ["/my/private_registration"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_private_registration(self, access_token=None, redirect=None, **kw):
        partner = request.env.user.partner_id
        values = self._membership_get_page_view_values(partner, access_token, **kw)
        product = self.get_private_membership_product()
        titles = request.env["res.partner.title"].sudo().search([])
        countries = request.env["res.country"].sudo().search([])
        teams = self._get_selected_team_id(partner)
        error = dict()
        error_message = []

        values.update(
            {
                "product": product,
                "total_membership": product.list_price,
                "dynamic_price": product.dynamic_price,
                "titles": titles,
                "countries": countries,
                "teams": teams,
                "error": error,
                "error_message": error_message,
            }
        )
        return request.render("lcc_members_portal.portal_private_registration", values)

    def _compute_private_form_data(self, data):
        values = {}
        for field in self._PRIVATE_REGISTRATION_FIELDS:
            if data.get(field):
                values[field] = data.pop(field)
        for field in self._EXTRA_FIELDS:
            if data.get(field):
                values[field] = data.pop(field)
        values["lastname"] = values["lastname"].upper()
        values["firstname"] = values["firstname"].title()
        values["name"] = values["firstname"] + " " + values["lastname"]
        values.update({"zip": values.pop("zipcode", "")})

        values["want_newsletter_subscription"] = (
            data.get("want_newsletter_subscription", "off") == "on"
        )
        values["accept_policy"] = data.get("accept_policy", "off") == "on"
        return values

    @http.route(
        ["/membership/subscribe_member"],
        type="http",
        auth="public",
        website=True,
    )
    def membership_subscription(self, **kwargs):
        # Update the partner data
        main_partner = request.env.user.partner_id
        values = self._compute_private_form_data(kwargs)
        main_partner.sudo().write(values)

        # Create sale order to finalize the registration process
        sale_order = request.website.sale_get_order(force_create=True)
        sale_order.company_id = main_partner.company_id.id
        sale_order.team_id = values["team_id"]
        values = {}
        values["member_product_id"] = self.get_private_membership_product().id
        if float(kwargs.get("total_membership", False)):
            values["total_membership"] = float(kwargs.get("total_membership"))
        else:
            values[
                "total_membership"
            ] = self.get_private_membership_product().list_price
        values["order_id"] = sale_order.id
        sale_order.sudo().create_membership(values)
        return request.redirect("/shop/cart")
