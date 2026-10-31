export type Category = { id: number; name: string; total_expenses: number };
export type Expense = { id: number; title: string; amount: number; category: string; created_at: string };
export type Summary = { total: number; count: number; average: number };

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(`Can't reach the API at ${API_URL}. Is the backend running?`);
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    const detail = typeof body?.detail === "string" ? body.detail : `Request failed (${response.status})`;
    throw new ApiError(detail);
  }
  return (await response.json()) as T;
}

export const api = {
  categories: () => request<Category[]>("/categories"),
  expenses: () => request<Expense[]>("/expenses"),
  summary: () => request<Summary>("/summary"),
  addCategory: (name: string) =>
    request<{ id: number; name: string }>("/categories", { method: "POST", body: JSON.stringify({ name }) }),
  addExpense: (input: { title: string; amount: number; category_id: number }) =>
    request<{ id: number }>("/expenses", { method: "POST", body: JSON.stringify(input) }),
};
