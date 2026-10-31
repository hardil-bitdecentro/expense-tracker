import { describe, expect, it } from "vitest";

import { validateCategory, validateExpense } from "./validation";

describe("validateExpense", () => {
  it("accepts a normal expense", () => {
    expect(validateExpense("Lunch", "250.50", "1")).toBeNull();
    expect(validateExpense("Lunch", "250", "1")).toBeNull();
    expect(validateExpense("Lunch", " 99.9 ", "1")).toBeNull();
  });

  it("needs a category first", () => {
    expect(validateExpense("Lunch", "10", "")).toBe("Pick a category first.");
  });

  it("rejects an empty or blank title", () => {
    expect(validateExpense("", "10", "1")).toBe("Give the expense a title.");
    expect(validateExpense("   ", "10", "1")).toBe("Give the expense a title.");
  });

  it("rejects a missing, zero or negative amount", () => {
    expect(validateExpense("Lunch", "", "1")).toBe("Enter an amount.");
    expect(validateExpense("Lunch", "0", "1")).toBe("Amount must be a positive number.");
    expect(validateExpense("Lunch", "0.00", "1")).toBe("Amount must be a positive number.");
    expect(validateExpense("Lunch", "-5", "1")).toBe("Amount must be a positive number.");
  });

  it("rejects amounts that are not plain numbers with up to two decimals", () => {
    for (const bad of ["abc", "10.555", "1e3", "10,5", "12345678901"]) {
      expect(validateExpense("Lunch", bad, "1")).toBe("Use a number with up to two decimals, like 250.50.");
    }
  });
});

describe("validateCategory", () => {
  it("accepts a new name", () => {
    expect(validateCategory("Groceries", ["Food"])).toBeNull();
  });

  it("rejects an empty name", () => {
    expect(validateCategory("  ", [])).toBe("Category name can't be empty.");
  });

  it("rejects a name that already exists, ignoring case and spaces", () => {
    expect(validateCategory("  food ", ["Food"])).toBe('"food" is already a category.');
  });
});
