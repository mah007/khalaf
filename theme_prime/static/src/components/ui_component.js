/** @odoo-module **/

import { registry } from "@web/core/registry";
import { AbstractComponent } from './abstract_component';
import { _t } from "@web/core/l10n/translation";

export class TpUiComponent extends AbstractComponent {
    setup() {
        this._coreProps = {
            changeValue: this._onChangeComponentValue.bind(this),
        };
        super.setup();
    }
    _onChangeComponentValue (value ,name) {
        this.env.updateUiComponentValue(name, value);
        // Ugly hack we should avoid it let's do the magic someday
        if (name === 'style' && this.stylesRegistry) {
            let config = this.stylesRegistry.get(value);
            if ('supportedActions' in config) {
                this.env.updateUiComponentValue('activeActions', [... this.actionProps.supportedActions]);
            }
        }
    }
    get supportedComponents() {
        let { defaultVal } = this.props.extras;
        return Object.keys(defaultVal);
    }
    get forceVisible() {
        let { forceVisible } = this.props.extras;
        return forceVisible || false;;
    }
    get noSelection() {
        let { noSelection } = this.props.extras;
        return noSelection || false;;
    }
    get stylesRegistry() {
        let { cardRegistry } = this.props.extras;
        return cardRegistry ? registry.category(cardRegistry) : false;
    }
    get componentRegistry() {
        return {
            TpDropDown: ['style', 'mode', 'header', 'productListing', 'childOrder', 'tabStyle', 'sortBy', 'mobileStyle', 'mobileMode'],
            TpRangeInput: ['ppr', 'limit'],
            TpBoolean: ['includesChild', 'bestseller', 'newArrived', 'discount', 'menuLabel', 'onlyDirectChild'],
            TpActions: ['activeActions'],
            TpCardGrid: ['categoryTabsConfig'],
            TpComponentGroup: ['mobileConfig'],
        }
    }
    get headers() {
        let headerRegistry = registry.category('theme_prime_product_list_cards_headers');
        return Object.keys(headerRegistry.content);
    }
    get styles() {
        return Object.keys(this.stylesRegistry.content);
    }
    get nodeOptions() {
        let buttonClasses = { buttonClasses: "btn d-flex justify-content-between align-items-center btn-default bg-white border shadow-sm fw-light w-100"};
        return { mobileConfig: { title: _t("Mobile Settings") }, style: { ...buttonClasses, title: _t("Style"), records: this.styles.map((style, index) => { return { id: style, title: _t(`Style - ${index + 1}`) };})}, mode: { ...buttonClasses, title: _t("Mode"), records: [{ id: 'grid', iconClass: 'fa fa-th-large pe-2', title: _t('Grid') }, { iconClass: 'fa pe-2 fa-arrows-h', id: 'slider', title: _t('Slider') }] }, header: { ...buttonClasses, title: _t("Header Style"), records: this.headers.map((header, index) => { return { id: header, title: _t(`Style - ${index + 1}`) }; })}, productListing: { ...buttonClasses, title: _t("Product Listing"), records: [{ iconClass: 'fa fa-percent', id: 'discount', title: _t("On Sale") }, { iconClass: 'fa fa-clock-o', id: 'newArrived', title: _t("Newly Arrived") }, { id: 'bestseller', iconClass: 'dri dri-bolt', title: _t("Bestseller") }] }, childOrder: { ...buttonClasses, title: _t("Child Order"), records: [{ id: 'count', title: _t("No. of Products") }, { id: 'sequence', title: _t("Sequence") }] }, tabStyle: { ...buttonClasses, title: _t("Tab Style"), records: [1, 2, 3, 4, 5, 6].map((style, index) => {return { id: `tp-droggol-builder-snippet-tab-${index + 1}`, title: _t(`Style - ${index + 1}`) };})},sortBy: { ...buttonClasses, title: _t("Sort by"), records: [{ id: 'list_price asc', iconClass: 'fa fa-sort-numeric-asc', title: _t("Price: Low to High") }, { id: 'list_price desc', iconClass: 'fa fa-sort-numeric-desc', title: _t("Price: High to Low") }, { id: 'name asc', iconClass: 'fa fa-sort-alpha-asc', title: _t("Name: A to Z") }, { id: 'name desc', iconClass: 'fa fa-sort-alpha-desc', title: _t("Name: Z to A") }, { iconClass: 'fa fa-clock-o', id: 'create_date desc', title: _t("Newly Arrived") }, { id: 'bestseller', iconClass: 'dri dri-bolt', title: _t("Bestseller") }] }, limit: { title: _t("No. of items"), maxValue: 20, minValue: 0 }, ppr: { title: _t('Product Per Row') }, includesChild: { title: _t('add Products From Child Categories') }, bestseller: { title: _t('Bestseller') }, newArrived: { title: _t('Newly Arrived') }, menuLabel: { title: _t('Display label') }, onlyDirectChild: { title: _t('Only Direct Child Categories') }, discount: { title: _t('On Sale')}, activeActions: this.actionProps, categoryTabsConfig: {}};
    }
    get componentDefaultVal() {
        return this.props.componentData;
    }
    get activeActions() {
        let item = this.stylesRegistry.get(this.componentDefaultVal.style);
        if (item.supportedActions) {
            return this.props.componentData.activeActions || [... this.stylesRegistry.get(this.componentDefaultVal.style).supportedActions];
        }
        return [];
    }
    get actionProps() {
        return {
            supportedActions: [... this.stylesRegistry.get(this.componentDefaultVal.style).supportedActions],
            activeActions: this.activeActions,
        }
    }
}
TpUiComponent.template = 'theme_prime.TpUiComponent';