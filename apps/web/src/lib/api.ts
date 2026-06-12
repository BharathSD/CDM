const API_BASE_URL = "http://localhost:4000";

export type Role = "ADMIN" | "EDITOR" | "VIEWER";

export type User = {
  id: string;
  username: string;
  role: Role;
};

export type Company = {
  id: string;
  cin: string;
  name: string;
  type: string;
  companyClass: string;
  status: string;
  registrationDate?: string | null;
  contactEmail?: string | null;
  contactPhone?: string | null;
  registeredAddress?: string | null;
  city?: string | null;
  state?: string | null;
  pincode?: string | null;
  panNumber?: string | null;
  gstNumber?: string | null;
  notes?: string | null;
};

type RequestOptions = {
  method?: "GET" | "POST" | "PUT";
  body?: unknown;
  token?: string;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Request failed");
  }

  return (await response.json()) as T;
}

export async function login(username: string, password: string) {
  return request<{ token: string; user: User }>("/auth/login", {
    method: "POST",
    body: { username, password },
  });
}

export async function getMe(token: string) {
  return request<User>("/auth/me", { token });
}

export async function getCompanies(token: string, query: string) {
  const params = new URLSearchParams();
  if (query.trim()) {
    params.set("query", query.trim());
  }
  return request<{ items: Company[]; total: number; page: number; pageSize: number }>(
    `/companies?${params.toString()}`,
    { token }
  );
}

export async function createCompany(token: string, payload: Partial<Company>) {
  return request<Company>("/companies", {
    method: "POST",
    token,
    body: payload,
  });
}

export async function updateCompany(token: string, id: string, payload: Partial<Company>) {
  return request<Company>(`/companies/${id}`, {
    method: "PUT",
    token,
    body: payload,
  });
}

// ─── Directors ───────────────────────────────────────────────────────────────

export type Director = {
  id: string;
  din: string;
  name: string;
  email?: string | null;
  phone?: string | null;
  status: string;
  notes?: string | null;
};

export async function getDirectors(token: string, query: string) {
  const params = new URLSearchParams();
  if (query.trim()) {
    params.set("query", query.trim());
  }
  return request<{ items: Director[]; total: number; page: number; pageSize: number }>(
    `/directors?${params.toString()}`,
    { token }
  );
}

export async function createDirector(token: string, payload: Partial<Director>) {
  return request<Director>("/directors", {
    method: "POST",
    token,
    body: payload,
  });
}

export async function updateDirector(token: string, id: string, payload: Partial<Director>) {
  return request<Director>(`/directors/${id}`, {
    method: "PUT",
    token,
    body: payload,
  });
}
