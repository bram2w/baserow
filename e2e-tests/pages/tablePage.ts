import {Locator, Page} from "@playwright/test";
import {BaserowPage} from "./baserowPage";

const TEST_IMAGE_FILE_PATH = 'assets/testuploadimage.png';

export class TablePage extends BaserowPage {
    private readonly projectsTextLocator: Locator;
    private readonly addColumnLocator: Locator;
    private readonly createButtonLocator: Locator;
    private readonly firstFileCellLocator: Locator;
    private readonly addFileLocator: Locator;
    private readonly fileZoneLocator: Locator;
    private readonly uploadButtonLocator: Locator;
    private readonly fileCellImageLocator: Locator;

    constructor(page: Page) {
        super(page);
        this.projectsTextLocator = this.page.locator('text=Projects');
        this.addColumnLocator = this.page.locator('.grid-view__add-column');
        this.createButtonLocator = this.page.getByRole('button', {name:/create/i});
        this.firstFileCellLocator = this.page.locator('.grid-field-file__cell').first();
        this.addFileLocator = this.page.locator('.grid-field-file__item-add');
        this.fileZoneLocator = this.page.locator('.upload-files__dropzone');
        this.uploadButtonLocator = this.page.locator('a').filter({ hasText: 'Upload' })
        this.fileCellImageLocator = this.page.locator('.grid-field-file__image');
    }

    async addNewFieldOfType(type: string) {
        await this.addColumnLocator.click();
        await this.page.locator(`.select__item-name-text[title="${type}"]`).click();
        await this.createButtonLocator.click()
    }

    async uploadImageToFirstFileFieldCellAndGetWidth(){
        await this.selectFirstFileCell();
        await this.clickAddFile();
        await this.uploadFile(TEST_IMAGE_FILE_PATH);
        return await this.getWidthOfFirstFileFieldCellImage();
    }
    async selectFirstFileCell() {
        await this.firstFileCellLocator.click();
    }

    async clickAddFile() {
        await this.addFileLocator.click();
    }

    async clickFileZone() {
        const clickFileZonePromise = this.fileZoneLocator.click();
        const fileChooserPromise = this.page.waitForEvent('filechooser');
        const [fileChooser] = await Promise.all([
            fileChooserPromise,
            clickFileZonePromise
        ]);
        return fileChooser;
    }

    async uploadFile(filePath) {
        const fileChooser = await this.clickFileZone();
        await fileChooser.setFiles(filePath);
        await this.uploadButtonLocator.click();
    }

    async waitForFileFieldCellImage() {
        await this.fileCellImageLocator.waitFor();
    }

    async getWidthOfFirstFileFieldCellImage() {
        await this.waitForFileFieldCellImage()
        return await this.page.evaluate(() => {
            const element = document.querySelector('.grid-field-file__image');
            return element.clientWidth;
        });
    }
}