import {Page} from "@playwright/test";
import {TemplateModal} from "./templateModal";

export class Sidebar {

    page: Page

    constructor(page: Page){
        this.page = page
    }
    sidebarCreateNewAppContextButton() {
        return this.page.locator('.sidebar__new').getByText("Create new")
    }

    fromTemplateContextButton() {
        return this.page.locator('.context__menu').getByText("From template")
    }

    async openCreateAppFromTemplateModal() : Promise<TemplateModal> {
        await this.sidebarCreateNewAppContextButton().click()
        await this.fromTemplateContextButton().click()
        return new TemplateModal(this.page)
    }
}