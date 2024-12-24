/** @odoo-module **/

import { registry } from "@web/core/registry";
import { SaleOrderFetcher } from "@pos_sale/app/order_management_screen/sale_order_fetcher/sale_order_fetcher";

class KhalafSaleOrderFetcher extends SaleOrderFetcher {
    async _getOrderIdsForCurrentPage(limit, offset) {
        const domain = [["currency_id", "=", this.pos.currency.id]].concat(this.searchDomain || []);

        this.pos.set_synch("connecting");
        const saleOrders = await this.orm.searchRead(
            "sale.order",
            domain,
            [
                "name",
                "partner_id",
                "amount_total",
                "date_order",
                "state",
                "user_id",
                "delivery_boy_id", // Fetch the delivery boy field
            ],
            { offset, limit }
        );

        this.pos.set_synch("connected");
        return saleOrders;
    }
}

registry.category("services").add("sale_order_fetcher", KhalafSaleOrderFetcher);
