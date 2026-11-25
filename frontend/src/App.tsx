import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Login } from './pages/Login';
import { Layout } from './components/Layout';
import { CambiarContrasena } from './pages/CambiarContrasena';
import { Empleados } from './pages/Empleados';
import { Stock } from './pages/Stock';
import { Caja } from './pages/Caja';
import { Ventas } from './pages/Ventas';

function RutaProtegida({ children }: { children: React.ReactNode }) {
  const { usuario } = useAuth();
  if (!usuario) return <Navigate to="/login" replace />;
  if (usuario.debeCambiarContrasena) return <Navigate to="/cambiar-contrasena" replace />;
  return <>{children}</>;
}

// Pantallas placeholder, se van a ir reemplazando modulo por modulo
function Coberturas() { return <h2>Coberturas (próximamente)</h2>; }
function Reportes() { return <h2>Reportes (próximamente)</h2>; }

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/cambiar-contrasena" element={<CambiarContrasena />} />
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
        <Route path="empleados" element={<Empleados />} />
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