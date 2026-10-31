import { expect, test } from "@playwright/test";

test("full flow: categories, expenses, validation, summary", async ({ page }) => {
  await page.goto("/");

  // Empty state before anything exists.
  await expect(page.getByText("Nothing recorded yet")).toBeVisible();
  await expect(page.getByRole("button", { name: "Add expense" })).toBeDisabled();

  const categoryError = page.locator("section", { hasText: "Categories" }).locator("p.error");
  const expenseError = page.locator("section", { hasText: "New expense" }).locator("p.error");

  // Create two categories, then try a duplicate.
  const categoryInput = page.getByLabel("New category name");
  for (const name of ["Food", "Travel"]) {
    await categoryInput.fill(name);
    await page.getByRole("button", { name: "Add", exact: true }).click();
    await expect(page.locator(".category-list")).toContainText(name);
  }
  await categoryInput.fill("food");
  await page.getByRole("button", { name: "Add", exact: true }).click();
  await expect(categoryError).toHaveText('"food" is already a category.');

  // Invalid expense input is caught before it is sent.
  const title = page.getByLabel("Title", { exact: true });
  const amount = page.getByLabel("Amount in rupees");
  const category = page.getByLabel("Category", { exact: true });
  const add = page.getByRole("button", { name: "Add expense" });

  await add.click();
  await expect(expenseError).toHaveText("Pick a category first.");

  await category.selectOption({ label: "Food" });
  await amount.fill("-20");
  await title.fill("Lunch");
  await add.click();
  await expect(expenseError).toHaveText("Amount must be a positive number.");

  // Two valid expenses.
  await amount.fill("250.5");
  await add.click();
  await expect(page.locator("tbody tr")).toHaveCount(1);

  await title.fill("Airport cab");
  await amount.fill("180");
  await category.selectOption({ label: "Travel" });
  await add.click();
  await expect(page.locator("tbody tr")).toHaveCount(2);

  // Newest first, with the category name and a date.
  const firstRow = page.locator("tbody tr").first();
  await expect(firstRow).toContainText("Airport cab");
  await expect(firstRow).toContainText("Travel");
  await expect(firstRow.locator("td.when")).not.toBeEmpty();

  // Summary matches the brief's example numbers.
  const figures = page.locator(".figures");
  await expect(figures).toContainText("₹430.50");
  await expect(figures).toContainText("2");
  await expect(figures).toContainText("₹215.25");

  // Category counts updated.
  await expect(page.locator(".category-list li", { hasText: "Food" })).toContainText("1 expense");
  await expect(page.locator(".category-list li", { hasText: "Travel" })).toContainText("1 expense");
});
