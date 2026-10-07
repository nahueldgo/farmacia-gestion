import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import type { Rol } from '../context/AuthContext';
import { API_URL } from '../config/api';

export function CambiarContrasena() {
  const { usuario, login } = useAuth();
  const navigate = useNavigate();
  const [contrasenaActual, setContrasenaActual] = useState('');
  const [contrasenaNueva, setContrasenaNueva] = useState('');
  const [repetir, setRepetir] = useState('');
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(false);

  // Sin sesion no hay nada que cambiar: vuelve al login
  if (!usuario) return <Navigate to="/login" replace />;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!contrasenaActual || !contrasenaNueva || !repetir) {
      setError('Completá los tres campos');
      return;
    }
    if (contrasenaNueva.length < 8) {
      setError('La contraseña nueva debe tener al menos 8 caracteres');
      return;
    }
    if (contrasenaNueva !== repetir) {
      setError('La contraseña nueva y su repetición no coinciden');
      return;
    }

    setCargando(true);
    try {
      const respuesta = await fetch(`${API_URL}/auth/contrasena`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${usuario.token}`,
        },
        body: JSON.stringify({
          contrasena_actual: contrasenaActual,
          contrasena_nueva: contrasenaNueva,
        }),
      });

      if (!respuesta.ok) {
        // Si el backend manda un mensaje en texto, lo mostramos
        const datos = await respuesta.json().catch(() => null);
        setError(
          typeof datos?.detail === 'string'
            ? datos.detail
            : `No se pudo cambiar la contraseña (${respuesta.status})`
        );
        return;
      }

      // El backend devuelve lo mismo que el login, con un token ya habilitado
      const datos = await respuesta.json();
      login(datos.nombre, datos.rol as Rol, datos.token, Boolean(datos.debeCambiarContrasena));
      navigate('/');
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setCargando(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '320px' }}>
        <h2>Cambiar contraseña</h2>
        <p style={{ fontSize: '14px', color: '#666' }}>
          Hola, {usuario.nombre}. Tenés que elegir una contraseña nueva antes de continuar.
        </p>

        <input
          type="password"
          placeholder="Contraseña actual"
          value={contrasenaActual}
          onChange={(e) => setContrasenaActual(e.target.value)}
        />
        <input
          type="password"
          placeholder="Contraseña nueva (mínimo 8 caracteres)"
          value={contrasenaNueva}
          onChange={(e) => setContrasenaNueva(e.target.value)}
        />
        <input
          type="password"
          placeholder="Repetir contraseña nueva"
          value={repetir}
          onChange={(e) => setRepetir(e.target.value)}
        />

        {error && <p style={{ color: 'red' }}>{error}</p>}

        <button type="submit" disabled={cargando}>
          {cargando ? 'Guardando...' : 'Cambiar contraseña'}
        </button>
      </form>
    </div>
  );
}