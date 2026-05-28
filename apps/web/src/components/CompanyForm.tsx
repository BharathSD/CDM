import { useMemo, useState } from "react";
import type { Company } from "../lib/api";

type CompanyFormProps = {
  initial?: Partial<Company>;
  onSubmit: (data: Partial<Company>) => Promise<void>;
  onCancel?: () => void;
  submitLabel: string;
};

const fields: Array<keyof Company> = [
  "cin",
  "name",
  "type",
  "companyClass",
  "status",
  "city",
  "state",
  "contactEmail",
  "contactPhone",
  "notes",
];

export function CompanyForm({ initial, onSubmit, onCancel, submitLabel }: CompanyFormProps) {
  const [form, setForm] = useState<Partial<Company>>({
    status: "active",
    ...initial,
  });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const requiredMissing = useMemo(() => {
    return !form.cin || !form.name || !form.type || !form.companyClass;
  }, [form]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    if (requiredMissing) {
      setError("CIN, Name, Type, and Class are required.");
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit(form);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Failed to save company");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="company-form" onSubmit={handleSubmit}>
      <div className="form-grid">
        {fields.map((field) => (
          <label key={field} className="field">
            <span>{field}</span>
            {field === "notes" ? (
              <textarea
                value={(form[field] as string | undefined) ?? ""}
                onChange={(e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))}
              />
            ) : (
              <input
                value={(form[field] as string | undefined) ?? ""}
                onChange={(e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))}
              />
            )}
          </label>
        ))}
      </div>
      {error ? <p className="error-text">{error}</p> : null}
      <div className="actions">
        {onCancel ? (
          <button type="button" className="secondary" onClick={onCancel}>
            Cancel
          </button>
        ) : null}
        <button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : submitLabel}
        </button>
      </div>
    </form>
  );
}
