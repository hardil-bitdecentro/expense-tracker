"use client";

import { useState, type FormEvent } from "react";

import { api, ApiError, type Category } from "@/lib/api";
import { plural } from "@/lib/format";
import { validateCategory } from "@/lib/validation";

type Props = { categories: Category[]; onSaved: () => Promise<void> };

export function CategoryPanel({ categories, onSaved }: Props) {
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const clean = name.trim();
    const problem = validateCategory(clean, categories.map((c) => c.name));
    if (problem) return setError(problem);

    setSaving(true);
    setError(null);
    try {
      await api.addCategory(clean);
      setName("");
      await onSaved();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add the category.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section>
      <h2>Categories</h2>
      <p className="note">Every expense belongs to one.</p>
      <form onSubmit={submit} noValidate>
        <div className="inline">
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Groceries" aria-label="New category name" maxLength={100} />
          <button className="button secondary" type="submit" disabled={saving}>
            Add
          </button>
        </div>
        {error && <p className="error" role="alert">{error}</p>}
      </form>

      {categories.length > 0 && (
        <ul className="category-list">
          {categories.map((c) => (
            <li key={c.id}>
              <span>{c.name}</span>
              <span className="count">{plural(c.total_expenses, "expense")}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
