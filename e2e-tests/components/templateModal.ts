import {Page} from "@playwright/test";

export class TemplateModal {
    page: Page

    constructor(page: Page){
        this.page = page
    }

    async waitUntilLoaded(){
        await this.page.locator('.templates__body .layout').waitFor()
    }

    loadingSpinner(){
        return this.page.locator('.modal__box .header__loading')
    }
}
