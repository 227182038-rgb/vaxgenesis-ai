export function formatDateTime(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleString();
}
export function formatNumber(n: number | null | undefined, digits = 2): string {
  if (n === null || n === undefined) return "—";
  return n.toFixed(digits);
}
