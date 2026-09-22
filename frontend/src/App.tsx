import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Login } from './pages/Login';
import { Layout } from './components/Layout';

function RutaProtegida({ children }: { children: React.ReactNode }) {
  const { usuario } = useAuth();
  if (!usuario) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

// Pantallas placeholder, se van a ir reemplazando modulo por modulo
function Ventas() { return <h2>Ventas (próximamente)</h2>; }
function Stock() { return <h2>Stock (próximamente)</h2>; }
function Coberturas() { return <h2>Coberturas (próximamente)</h2>; }
function Caja() { return <h2>Caja (próximamente)</h2>; }
function Reportes() { return <h2>Reportes (próximamente)</h2>; }

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <RutaProtegida>
            <Layout />
          </RutaProtegida>
        }
      >
        <Route index element={<Navigate to="/ventas" replace />} />
        <Route path="ventas" element={<Ventas />} />
        <Route path="stock" element={<Stock />} />
        <Route path="coberturas" element={<Coberturas />} />
        <Route path="caja" element={<Caja />} />
        <Route path="reportes" element={<Reportes />} />
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;