import type { Summary } from "@/lib/api";
import { formatMoney } from "@/lib/format";

export function SummaryFigures({ summary }: { summary: Summary | null }) {
  const placeholder = "—";
  return (
    <dl className="figures">
      <div className="figure">
        <dt>Total spent</dt>
        <dd>{summary ? formatMoney(summary.total) : placeholder}</dd>
      </div>
      <div className="figure">
        <dt>Expenses</dt>
        <dd>{summary ? summary.count : placeholder}</dd>
      </div>
      <div className="figure">
        <dt>Average</dt>
        <dd>{summary ? formatMoney(summary.average) : placeholder}</dd>
      </div>
    </dl>
  );
}
