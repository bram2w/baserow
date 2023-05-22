import {Locator, Page} from "@playwright/test";

export class TemplateModal {
    private readonly page: Page;
    private readonly templateBodyLayout: Locator;
    private readonly modelLoadingSpinner: Locator;
    private readonly useThisTemplateButton: Locator;
    private closeNotificationLocator: Locator;

    constructor(page: Page) {
        this.page = page;
        this.templateBodyLayout = this.page.locator('.templates__body .layout');
        this.modelLoadingSpinner = this.page.locator('.modal__box .header__loading');
        this.useThisTemplateButton = this.page.getByText(/use this template/i)
        this.closeNotificationLocator = this.page.locator('.alert__close')
    }

    async waitUntilLoaded() {
        await this.templateBodyLayout.waitFor();
    }

    loadingSpinner() {
        return this.modelLoadingSpinner;
    }

    async clickUseThisTemplateButton() {
        await this.useThisTemplateButton.click();
        await this.closeNotificationLocator.click();
    }
}
