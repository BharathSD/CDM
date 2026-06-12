import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CompanyForm } from "../components/CompanyForm";
import { DirectorsPage } from "./DirectorsPage";
import { createCompany, getCompanies, updateCompany, type Company, type Role } from "../lib/api";

type DashboardPageProps = {
  auth: {
    token: string | null;
    user: { id: string; username: string; role: Role } | null;
    logout: () => void;
  };
};

export function DashboardPage({ auth }: DashboardPageProps) {
  const [activeTab, setActiveTab] = useState<"companies" | "directors">("companies");
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<Company | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const canEdit = auth.user?.role === "ADMIN" || auth.user?.role === "EDITOR";

  const companiesQuery = useQuery({
    queryKey: ["companies", query],
    queryFn: () => getCompanies(auth.token!, query),
    enabled: Boolean(auth.token),
  });

  const createMutation = useMutation({
    mutationFn: (payload: Partial<Company>) => createCompany(auth.token!, payload),
    onSuccess: (company) => {
      setShowCreate(false);
      setSuccessMessage(`Company "${company.name}" added successfully.`);
      setTimeout(() => setSuccessMessage(null), 4000);
      queryClient.invalidateQueries({ queryKey: ["companies"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<Company> }) =>
      updateCompany(auth.token!, id, payload),
    onSuccess: () => {
      setEditing(null);
      queryClient.invalidateQueries({ queryKey: ["companies"] });
    },
  });

  const rows = useMemo(() => companiesQuery.data?.items ?? [], [companiesQuery.data]);

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div>
          <h1>CDM Portal</h1>
          <p>Track, search, and maintain company and director records</p>
        </div>
        <div className="header-actions">
          <span className="badge">{auth.user?.role}</span>
          <button className="secondary" onClick={auth.logout}>
            Logout
          </button>
        </div>
      </header>

      <div className="tab-bar">
        <button
          className={activeTab === "companies" ? "tab-btn tab-btn--active" : "tab-btn"}
          onClick={() => setActiveTab("companies")}
        >
          Company Registry
        </button>
        <button
          className={activeTab === "directors" ? "tab-btn tab-btn--active" : "tab-btn"}
          onClick={() => setActiveTab("directors")}
        >
          Director Registry
        </button>
      </div>

      {activeTab === "directors" ? (
        <DirectorsPage auth={auth} />
      ) : (
        <div style={{ display: "grid", gap: "1rem" }}>
          <section className="card toolbar">
            <input
              placeholder="Search by CIN or company name"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            {canEdit ? <button onClick={() => setShowCreate((v) => !v)}>{showCreate ? "Close" : "Add Company"}</button> : null}
          </section>

          {successMessage ? (
            <section className="card" style={{ borderLeft: "4px solid #22c55e", color: "#166534" }}>
              {successMessage}
            </section>
          ) : null}

          {showCreate && canEdit ? (
            <section className="card">
              <h2>Add Company</h2>
              <CompanyForm
                submitLabel="Create Company"
                onSubmit={(data) => createMutation.mutateAsync(data)}
                onCancel={() => setShowCreate(false)}
              />
            </section>
          ) : null}

          {editing && canEdit ? (
            <section className="card">
              <h2>Edit Company</h2>
              <CompanyForm
                initial={editing}
                submitLabel="Update Company"
                onSubmit={(data) => updateMutation.mutateAsync({ id: editing.id, payload: data })}
                onCancel={() => setEditing(null)}
              />
            </section>
          ) : null}

          <section className="card">
            <h2>Companies</h2>
            {companiesQuery.isLoading ? <p>Loading companies...</p> : null}
            {companiesQuery.isError ? <p className="error-text">{(companiesQuery.error as Error).message}</p> : null}
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>CIN</th>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Class</th>
                    <th>Status</th>
                    <th>City</th>
                    <th>State</th>
                    {canEdit ? <th>Action</th> : null}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((company) => (
                    <tr key={company.id}>
                      <td>{company.cin}</td>
                      <td>{company.name}</td>
                      <td>{company.type}</td>
                      <td>{company.companyClass}</td>
                      <td>{company.status}</td>
                      <td>{company.city ?? "-"}</td>
                      <td>{company.state ?? "-"}</td>
                      {canEdit ? (
                        <td>
                          <button className="secondary" onClick={() => setEditing(company)}>
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
      )}
    </div>
  );
}
