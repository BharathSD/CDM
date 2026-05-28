import { Navigate, Route, Routes } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { getMe, type User } from "./lib/api";

export function App() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("token"));
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(Boolean(token));

  useEffect(() => {
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    getMe(token)
      .then((nextUser) => setUser(nextUser))
      .catch(() => {
        setToken(null);
        localStorage.removeItem("token");
      })
      .finally(() => setLoading(false));
  }, [token]);

  const auth = useMemo(
    () => ({
      token,
      user,
      login: (nextToken: string, nextUser: User) => {
        localStorage.setItem("token", nextToken);
        setToken(nextToken);
        setUser(nextUser);
      },
      logout: () => {
        localStorage.removeItem("token");
        setToken(null);
        setUser(null);
      },
    }),
    [token, user]
  );

  if (loading) {
    return <div className="screen-center">Loading portal...</div>;
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={token && user ? <Navigate to="/" replace /> : <LoginPage auth={auth} />}
      />
      <Route
        path="/"
        element={
          token && user ? (
            <DashboardPage auth={auth} />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route path="*" element={<Navigate to={token ? "/" : "/login"} replace />} />
    </Routes>
  );
}
