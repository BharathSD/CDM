import { useState } from "react";
import { login } from "../lib/api";

type LoginPageProps = {
  auth: {
    login: (token: string, user: { id: string; username: string; role: "ADMIN" | "EDITOR" | "VIEWER" }) => void;
  };
};

export function LoginPage({ auth }: LoginPageProps) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleLogin(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const result = await login(username, password);
      auth.login(result.token, result.user);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <section className="card">
        <h1>CDM Portal</h1>
        <p>Income tax company management dashboard</p>
        <form className="login-form" onSubmit={handleLogin}>
          <label>
            Username
            <input value={username} onChange={(e) => setUsername(e.target.value)} />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error ? <p className="error-text">{error}</p> : null}
          <button type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </section>
    </main>
  );
}
