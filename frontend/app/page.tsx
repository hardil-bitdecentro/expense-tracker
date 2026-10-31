"use client";

import { useCallback, useEffect, useState } from "react";

import { CategoryPanel } from "@/components/CategoryPanel";
import { ExpenseForm } from "@/components/ExpenseForm";
import { ExpenseTable } from "@/components/ExpenseTable";
import { SummaryFigures } from "@/components/SummaryFigures";
import { api, ApiError, type Category, type Expense, type Summary } from "@/lib/api";

const today = new Intl.DateTimeFormat("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" });

export default function Home() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  // One refresh after every change keeps the list, the counts and the totals in step.
  const refresh = useCallback(async () => {
    try {
      const [c, e, s] = await Promise.all([api.categories(), api.expenses(), api.summary()]);
      setCategories(c);
      setExpenses(e);
      setSummary(s);
      setLoadError(null);
    } catch (err) {
      setLoadError(err instanceof ApiError ? err.message : "Something went wrong while loading.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <main className="page">
      <header className="masthead">
        <div>
          <h1>Expenses</h1>
          <p>Where the money went, by category.</p>
        </div>
        <time suppressHydrationWarning>{today.format(new Date())}</time>
      </header>

      <SummaryFigures summary={summary} />

      {loadError && <p className="error banner">{loadError}</p>}

      <div className="columns">
        <aside className="side">
          <ExpenseForm categories={categories} onSaved={refresh} />
          <CategoryPanel categories={categories} onSaved={refresh} />
        </aside>

        <ExpenseTable expenses={expenses} loading={loading} />
      </div>
    </main>
  );
}
