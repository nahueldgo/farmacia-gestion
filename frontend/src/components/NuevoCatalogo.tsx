import { useState } from 'react';
import { API_URL } from '../config/api';

export interface NuevoElemento {
  id: number;
  nombre: string;
}

interface Props {
  token: string;
  ruta: 'laboratorios' | 'principios-activos';
  campoId: 'id_laboratorio' | 'id_principio_activo';
  etiqueta: string; // por ejemplo "laboratorio"
  alCrear: (nuevo: NuevoElemento) => void;
}

export function NuevoCatalogo({ token, ruta, campoId, etiqueta, alCrear }: Props) {
  const [abierto, setAbierto] = useState(false);
  const [nombre, setNombre] = useState('');
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  function cerrar() {
    setAbierto(false);
    setNombre('');
    setError('');
  }

  async function crear() {
    setError('');
    if (!nombre.trim()) {
      setError(`Escribí el nombre del ${etiqueta}.`);
      return;
    }
    setEnviando(true);
    try {
      const respuesta = await fetch(`${API_URL}/catalogos/${ruta}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ nombre: nombre.trim() }),
      });
      if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setError(`No tenés permiso para crear un ${etiqueta}.`);
      } else if (!respuesta.ok) {
        let mensaje = `No se pudo crear el ${etiqueta}.`;
        try {
          const datos = await respuesta.json();
          if (typeof datos.detail === 'string') mensaje = datos.detail;
          else if (Array.isArray(datos.detail) && datos.detail[0]?.msg) mensaje = datos.detail[0].msg;
        } catch {
          // si la respuesta no es JSON, dejamos el mensaje por defecto
        }
        setError(mensaje);
      } else {
        const datos = await respuesta.json();
        alCrear({ id: datos[campoId], nombre: datos.nombre });
        cerrar();
      }
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setEnviando(false);
    }
  }

  if (!abierto) {
    return (
      <button type="button" onClick={() => setAbierto(true)}>
        + Nuevo
      </button>
    );
  }

  return (
    <span>
      <input
        value={nombre}
        placeholder={`Nombre del ${etiqueta}`}
        onChange={(e) => setNombre(e.target.value)}
        onKeyDown={(e) => {
          // Dentro de un formulario, Enter lo enviaría: lo usamos para crear el elemento
          if (e.key === 'Enter') {
            e.preventDefault();
            crear();
          }
        }}
        autoFocus
      />{' '}
      <button type="button" onClick={crear} disabled={enviando}>
        {enviando ? 'Creando...' : 'Crear'}
      </button>{' '}
      <button type="button" onClick={cerrar} disabled={enviando}>
        Cancelar
      </button>
      {error && <span style={{ color: 'crimson', display: 'block' }}>{error}</span>}
    </span>
  );
}