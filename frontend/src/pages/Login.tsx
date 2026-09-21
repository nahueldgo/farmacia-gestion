import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function Login() {
  const [nombreUsuario, setNombreUsuario] = useState('');
  const [contrasena, setContrasena] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!nombreUsuario || !contrasena) {
      setError('Completá usuario y contraseña');
      return;
    }

    // SIMULACION: aca va a ir el fetch real al backend (POST /login)
    // cuando el endpoint este listo. Por ahora, simulamos un login
    // exitoso con un rol fijo para poder probar el resto de la app.
    login(nombreUsuario, 'farmaceutico');
    navigate('/');
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '300px' }}>
        <h2>Sistema Farmacia</h2>

        <input
          type="text"
          placeholder="Usuario"
          value={nombreUsuario}
          onChange={(e) => setNombreUsuario(e.target.value)}
        />

        <input
          type="password"
          placeholder="Contraseña"
          value={contrasena}
          onChange={(e) => setContrasena(e.target.value)}
        />

        {error && <p style={{ color: 'red' }}>{error}</p>}

        <button type="submit">Ingresar</button>
      </form>
    </div>
  );
}