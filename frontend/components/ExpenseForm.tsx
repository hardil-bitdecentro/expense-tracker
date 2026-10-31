"use client";

import { useState, type FormEvent } from "react";

import { api, ApiError, type Category } from "@/lib/api";
import { validateExpense } from "@/lib/validation";

type Props = { categories: Category[]; onSaved: () => Promise<void> };

export function ExpenseForm({ categories, onSaved }: Props) {
  const [title, setTitle] = useState("");
  const [amount, setAmount] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const noCategories = categories.length === 0;

  async function submit(event: FormEvent) {
    event.preventDefault();
    const problem = validateExpense(title, amount, categoryId);
    if (problem) return setError(problem);

    setSaving(true);
    setError(null);
    try {
      await api.addExpense({ title: title.trim(), amount: Number(amount.trim()), category_id: Number(categoryId) });
      setTitle("");
      setAmount("");
      await onSaved();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save the expense.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section>
      <h2>New expense</h2>
      <p className="note">{noCategories ? "Add a category below before your first expense." : "It shows up in the list straight away."}</p>
      <form onSubmit={submit} noValidate>
        <label>
          Title
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Lunch with the team" maxLength={200} />
        </label>
        <label>
          Amount
          <span className="amount-field">
            <span aria-hidden>₹</span>
            <input
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              inputMode="decimal"
              placeholder="0.00"
              aria-label="Amount in rupees"
            />
          </span>
        </label>
        <label>
          Category
          <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)} disabled={noCategories} aria-label="Category">
            <option value="">{noCategories ? "No categories yet" : "Choose a category"}</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button className="button" type="submit" disabled={saving || noCategories}>
          {saving ? "Saving…" : "Add expense"}
        </button>
      </form>
    </section>
  );
}
