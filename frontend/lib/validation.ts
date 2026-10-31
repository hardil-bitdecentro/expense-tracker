// The same rules the API enforces, checked in the form first for instant feedback.
// Each function returns an error message, or null when the input is fine.

const AMOUNT_PATTERN = /^\d{1,10}(\.\d{1,2})?$/;

export function validateExpense(title: string, amount: string, categoryId: string): string | null {
  if (!categoryId) return "Pick a category first.";
  if (!title.trim()) return "Give the expense a title.";

  const raw = amount.trim();
  if (!raw) return "Enter an amount.";
  if (!AMOUNT_PATTERN.test(raw)) {
    return /^-/.test(raw) ? "Amount must be a positive number." : "Use a number with up to two decimals, like 250.50.";
  }
  if (Number(raw) <= 0) return "Amount must be a positive number.";
  return null;
}

export function validateCategory(name: string, existing: readonly string[]): string | null {
  const clean = name.trim();
  if (!clean) return "Category name can't be empty.";
  if (existing.some((n) => n.toLowerCase() === clean.toLowerCase())) return `"${clean}" is already a category.`;
  return null;
}
