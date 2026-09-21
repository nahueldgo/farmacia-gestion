import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function Home() {
  const { usuario, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Sistema Farmacia</h1>
      <p>Hola, {usuario?.nombre} (rol: {usuario?.rol})</p>
      <button onClick={handleLogout}>Cerrar sesión</button>
    </div>
  );
}