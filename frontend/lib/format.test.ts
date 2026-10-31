import { describe, expect, it } from "vitest";

import { formatMoney, formatWhen, plural } from "./format";

describe("formatMoney", () => {
  it("shows rupees with two decimals and Indian grouping", () => {
    expect(formatMoney(250.5)).toBe("₹250.50");
    expect(formatMoney(123456.7)).toBe("₹1,23,456.70");
    expect(formatMoney(0)).toBe("₹0.00");
  });
});

describe("formatWhen", () => {
  it("treats timestamps without an offset as UTC", () => {
    expect(formatWhen("2026-04-14T12:00:00")).toBe(formatWhen("2026-04-14T12:00:00Z"));
  });

  it("leaves timestamps with an offset alone", () => {
    expect(formatWhen("2026-04-14T17:30:00+05:30")).toBe(formatWhen("2026-04-14T12:00:00Z"));
  });
});

describe("plural", () => {
  it("uses the singular only for one", () => {
    expect(plural(1, "expense")).toBe("1 expense");
    expect(plural(0, "expense")).toBe("0 expenses");
    expect(plural(3, "entry", "entries")).toBe("3 entries");
  });
});
