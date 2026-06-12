import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { DirectorForm } from "../components/DirectorForm";
import { createDirector, getDirectors, updateDirector, type Director, type Role } from "../lib/api";

type DirectorsPageProps = {
  auth: {
    token: string | null;
    user: { id: string; username: string; role: Role } | null;
  };
};

export function DirectorsPage({ auth }: DirectorsPageProps) {
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<Director | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const canEdit = auth.user?.role === "ADMIN" || auth.user?.role === "EDITOR";

  const directorsQuery = useQuery({
    queryKey: ["directors", query],
    queryFn: () => getDirectors(auth.token!, query),
    enabled: Boolean(auth.token),
  });

  const createMutation = useMutation({
    mutationFn: (payload: Partial<Director>) => createDirector(auth.token!, payload),
    onSuccess: (director) => {
      setShowCreate(false);
      setSuccessMessage(`Director "${director.name}" added successfully.`);
      setTimeout(() => setSuccessMessage(null), 4000);
      queryClient.invalidateQueries({ queryKey: ["directors"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<Director> }) =>
      updateDirector(auth.token!, id, payload),
    onSuccess: () => {
      setEditing(null);
      queryClient.invalidateQueries({ queryKey: ["directors"] });
    },
  });

  const rows = useMemo(() => directorsQuery.data?.items ?? [], [directorsQuery.data]);

  return (
    <div style={{ display: "grid", gap: "1rem" }}>
      <section className="card toolbar">
        <input
          placeholder="Search by DIN or director name"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {canEdit ? (
          <button onClick={() => setShowCreate((v) => !v)}>
            {showCreate ? "Close" : "Add Director"}
          </button>
        ) : null}
      </section>

      {successMessage ? (
        <section className="card" style={{ borderLeft: "4px solid #22c55e", color: "#166534" }}>
          {successMessage}
        </section>
      ) : null}

      {showCreate && canEdit ? (
        <section className="card">
          <h2>Add Director</h2>
          <DirectorForm
            submitLabel="Create Director"
            onSubmit={(data) => createMutation.mutateAsync(data)}
            onCancel={() => setShowCreate(false)}
          />
        </section>
      ) : null}

      {editing && canEdit ? (
        <section className="card">
          <h2>Edit Director</h2>
          <DirectorForm
            initial={editing}
            submitLabel="Update Director"
            onSubmit={(data) => updateMutation.mutateAsync({ id: editing.id, payload: data })}
            onCancel={() => setEditing(null)}
          />
        </section>
      ) : null}

      <section className="card">
        <h2>Directors</h2>
        {directorsQuery.isLoading ? <p>Loading directors...</p> : null}
        {directorsQuery.isError ? (
          <p className="error-text">{(directorsQuery.error as Error).message}</p>
        ) : null}
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>DIN</th>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Status</th>
                {canEdit ? <th>Action</th> : null}
              </tr>
            </thead>
            <tbody>
              {rows.map((director) => (
                <tr key={director.id}>
                  <td>{director.din}</td>
                  <td>{director.name}</td>
                  <td>{director.email ?? "-"}</td>
                  <td>{director.phone ?? "-"}</td>
                  <td>{director.status}</td>
                  {canEdit ? (
                    <td>
                      <button className="secondary" onClick={() => setEditing(director)}>
                        Edit
                      </button>
                    </td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
