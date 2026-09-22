import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { menuPorRol } from '../config/menuPorRol';

export function Layout() {
  const { usuario, logout } = useAuth();

  if (!usuario) return null;

  const opciones = menuPorRol[usuario.rol] || [];

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <nav style={{ width: '220px', borderRight: '1px solid #ccc', padding: '16px' }}>
        <h3>Sistema Farmacia</h3>
        <p style={{ fontSize: '14px', color: '#666' }}>
          {usuario.nombre} ({usuario.rol})
        </p>

        <ul style={{ listStyle: 'none', padding: 0 }}>
          {opciones.map((item) => (
            <li key={item.path} style={{ marginBottom: '8px' }}>
              <NavLink to={item.path}>{item.label}</NavLink>
            </li>
          ))}
        </ul>

        <button onClick={logout}>Cerrar sesión</button>
      </nav>

      <main style={{ flex: 1, padding: '20px' }}>
        <Outlet />  {/* <Outlet /> Significa "aca se va a insertar el contenido de la pantalla que corresponda
                    segun la ruta, el menu queda fijo a la izquierda y el contenido cambia a la derecha
                    segun que opcion toque el usuario.*/}
      </main>
    </div>
  );
}