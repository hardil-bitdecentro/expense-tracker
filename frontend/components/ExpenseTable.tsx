import type { Expense } from "@/lib/api";
import { formatMoney, formatWhen, plural } from "@/lib/format";

export function ExpenseTable({ expenses, loading }: { expenses: Expense[]; loading: boolean }) {
  return (
    <section>
      <div className="ledger-head">
        <h2>All expenses</h2>
        {!loading && <span className="note">{plural(expenses.length, "entry", "entries")}, newest first</span>}
      </div>

      {loading ? (
        <p className="muted">Loading…</p>
      ) : expenses.length === 0 ? (
        <div className="empty">
          <strong>Nothing recorded yet</strong>
          Add a category, then your first expense on the left.
        </div>
      ) : (
        <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Title</th>
              <th>Category</th>
              <th className="num">Amount</th>
            </tr>
          </thead>
          <tbody>
            {expenses.map((e) => (
              <tr key={e.id}>
                <td className="when">{formatWhen(e.created_at)}</td>
                <td>{e.title}</td>
                <td className="tag">{e.category}</td>
                <td className="num">{formatMoney(e.amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      )}
    </section>
  );
}
