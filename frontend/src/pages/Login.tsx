import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import type { Rol } from '../context/AuthContext';
import { API_URL } from '../config/api';

export function Login() {
  const [nombreUsuario, setNombreUsuario] = useState('');
  const [contrasena, setContrasena] = useState('');
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!nombreUsuario || !contrasena) {
      setError('Completá usuario y contraseña');
      return;
    }

    setCargando(true);
    try {
      const respuesta = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombreUsuario, contrasena }),
      });

      if (respuesta.status === 401) {
        setError('Usuario o contraseña incorrectos');
        return;
      }

      if (!respuesta.ok) {
        setError(`El servidor respondió con un error (${respuesta.status})`);
        return;
      }

      const datos = await respuesta.json();
      login(datos.nombre, datos.rol as Rol, datos.token, Boolean(datos.debeCambiarContrasena));
      navigate(datos.debeCambiarContrasena ? '/cambiar-contrasena' : '/');
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setCargando(false);
    }
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

        <button type="submit" disabled={cargando}>
          {cargando ? 'Ingresando...' : 'Ingresar'}
        </button>
      </form>
    </div>
  );
}