import { useMemo, useState } from "react";
import type { Director } from "../lib/api";

type DirectorFormProps = {
  initial?: Partial<Director>;
  onSubmit: (data: Partial<Director>) => Promise<void>;
  onCancel?: () => void;
  submitLabel: string;
};

const fieldLabels: Record<keyof Omit<Director, "id">, string> = {
  din: "DIN (Director Identification Number)",
  name: "Full Name",
  email: "Email ID",
  phone: "Phone Number",
  status: "Status",
  notes: "Notes",
};

const fieldKeys = ["din", "name", "email", "phone", "status", "notes"] as const;

export function DirectorForm({ initial, onSubmit, onCancel, submitLabel }: DirectorFormProps) {
  const [form, setForm] = useState<Partial<Director>>({
    status: "active",
    ...initial,
  });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const requiredMissing = useMemo(() => {
    return !form.din || !form.name;
  }, [form]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    if (requiredMissing) {
      setError("DIN and Name are required.");
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit(form);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Failed to save director");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="company-form" onSubmit={handleSubmit}>
      <div className="form-grid">
        {fieldKeys.map((field) => (
          <label key={field} className="field">
            <span>{fieldLabels[field]}</span>
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
