/**
 * Button field, start workflow action: who started the run.
 *
 * The backend tests prove the history row names the clicker and the unit test
 * proves the panel renders a name it is given. Nothing below this file runs
 * the whole loop: an editor's real click, the real Celery worker running the
 * workflow, and a builder reading "Started by" in the History panel.
 */

import { Page } from "@playwright/test";
import { test, expect } from "../baserowTest";
import { GridPage } from "../../pages/database/gridPage";
import { AutomationWorkflowPage } from "../../pages/automation/automationWorkflowPage";
import { PageConfig } from "../../pages/baserowPage";
import { setupGrid, GridSetupResult } from "../../fixtures/database/gridSetup";
import { createStartWorkflowAction } from "../../fixtures/database/workflowAction";
import { createAutomation } from "../../fixtures/automation/automation";
import {
  AutomationWorkflow,
  createAutomationWorkflow,
  publishAutomationWorkflow,
} from "../../fixtures/automation/automationWorkflow";
import { createAutomationNode } from "../../fixtures/automation/automationNode";
import { User, createUser } from "../../fixtures/user";
import { addUserToWorkspace } from "../../fixtures/workspace";

// Position in the right-hand section, the only field `beforeAll` creates.
const START_FIELD_INDEX = 0;

let g: GridSetupResult;
let workflow: AutomationWorkflow;
/** A member of the workspace who can click the button but not open the automation. */
let editor: User;

/**
 * The builder on the workflow page, with the AI panel kept shut so it does not
 * sit over the header's buttons.
 */
async function builderOnWorkflow(page: Page, goto: PageConfig["goto"]) {
  const workflowPage = new AutomationWorkflowPage(
    { page, goto },
    workflow.automation,
    workflow
  );
  await workflowPage.authenticate(g.user);
  await page.evaluate(() => {
    localStorage.setItem("baserow.rightSidebarOpen", "false");
  });
  await workflowPage.goto();
  return workflowPage;
}

async function openHistoryPanel(page: Page) {
  await page.locator('[data-item-type="history"]').click();
  await expect(page.locator(".history-side-panel__title")).toBeVisible();
}

/** The history entries in the panel, newest first, as the panel orders them. */
function historyEntries(page: Page) {
  return page.locator(".workflow-history__header");
}

test.describe("Button field, start workflow action", () => {
  test.beforeAll(async () => {
    g = await setupGrid({
      dbName: "Start workflow DB",
      tableName: "Jobs",
      fields: [{ name: "Start", type: "button", settings: { label: "Start" } }],
      rows: [{ Name: "row one" }],
    });

    const automation = await createAutomation(
      "Start workflow automation",
      g.database.workspace
    );
    workflow = await createAutomationWorkflow("Started by button", automation);
    await createAutomationNode(workflow, "manual");
    await publishAutomationWorkflow(workflow);
    await createStartWorkflowAction(
      g.user,
      g.fieldByName["Start"],
      workflow.id
    );

    editor = await createUser();
    await addUserToWorkspace(g.user, g.database.workspace, editor, "MEMBER");
  });

  test("a click by an editor shows up as started by them in the workflow history", async ({
    page,
    browser,
    goto,
  }) => {
    // The editor clicks, in their own browser.
    const editorContext = await browser.newContext();
    try {
      const editorPage = await editorContext.newPage();
      const grid = new GridPage(editorPage, editor);
      await grid.goTo(g.database, g.table);
      await grid.fieldCellAt(0, START_FIELD_INDEX).locator("button").click();
      // The cell settles once the dispatch has returned.
      await expect(
        grid.fieldCellAt(0, START_FIELD_INDEX).locator("button")
      ).toBeEnabled();
    } finally {
      await editorContext.close();
    }

    // The builder, who owns the automation, reads the run's history.
    await builderOnWorkflow(page, goto);
    await openHistoryPanel(page);

    const entry = historyEntries(page).first();
    await expect(entry.locator(".workflow-history__header-actor")).toHaveText(
      `Started by ${editor.name}`
    );
    // Not a test run: no prefix on the title. The worker in the e2e stack
    // runs the workflow for real, so it also completes.
    await expect(entry.locator(".workflow-history__header-title")).toHaveText(
      "Ran successfully"
    );
  });

  test("a test run from the editor is started by whoever pressed the button", async ({
    page,
    goto,
  }) => {
    await builderOnWorkflow(page, goto);

    await page.locator('[data-highlight="automation-test-run"]').click();
    await openHistoryPanel(page);

    const entry = historyEntries(page).first();
    await expect(
      entry.locator(".workflow-history__header-title")
    ).toContainText("[Test]");
    await expect(entry.locator(".workflow-history__header-actor")).toHaveText(
      `Started by ${g.user.name}`
    );
  });
});
