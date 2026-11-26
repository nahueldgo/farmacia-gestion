import { useState } from 'react';
import { API_URL } from '../config/api';

export interface ClienteElegido {
  id_cliente: number;
  nombre: string;
  apellido: string;
  dni: string;
  telefono: string | null;
}

interface Props {
  token: string;
  cliente: ClienteElegido | null;
  alElegir: (cliente: ClienteElegido | null) => void;
}

function mensajeDeError(datos: unknown, porDefecto: string) {
  const detail = (datos as { detail?: unknown })?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && typeof detail[0]?.msg === 'string') return detail[0].msg;
  return porDefecto;
}

export function ClienteVenta({ token, cliente, alElegir }: Props) {
  const [dni, setDni] = useState('');
  const [buscando, setBuscando] = useState(false);
  const [noEncontrado, setNoEncontrado] = useState(false);
  const [error, setError] = useState('');

  // Datos del alta rápida
  const [nombre, setNombre] = useState('');
  const [apellido, setApellido] = useState('');
  const [telefono, setTelefono] = useState('');
  const [creando, setCreando] = useState(false);

  // Aceptamos el DNI con puntos o espacios y lo usamos solo con números
  const dniLimpio = dni.replace(/[.\s]/g, '');

  async function buscar() {
    setError('');
    setNoEncontrado(false);
    if (!/^\d{7,8}$/.test(dniLimpio)) {
      setError('El DNI tiene que tener 7 u 8 números.');
      return;
    }
    setBuscando(true);
    try {
      const respuesta = await fetch(`${API_URL}/clientes/dni/${dniLimpio}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (respuesta.status === 404) {
        setNoEncontrado(true);
      } else if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setError('No tenés permiso para buscar clientes.');
      } else if (!respuesta.ok) {
        setError('No se pudo buscar el cliente.');
      } else {
        alElegir(await respuesta.json());
        setDni('');
      }
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setBuscando(false);
    }
  }

  async function crear() {
    setError('');
    if (!nombre.trim() || !apellido.trim()) {
      setError('El nombre y el apellido son obligatorios.');
      return;
    }
    const cuerpo: Record<string, string> = {
      nombre: nombre.trim(),
      apellido: apellido.trim(),
      dni: dniLimpio,
    };
    if (telefono.trim()) cuerpo.telefono = telefono.trim();

    setCreando(true);
    try {
      const respuesta = await fetch(`${API_URL}/clientes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(cuerpo),
      });
      if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (respuesta.status === 403) {
        setError('No tenés permiso para cargar clientes.');
      } else if (!respuesta.ok) {
        let datos: unknown = null;
        try {
          datos = await respuesta.json();
        } catch {
          // si la respuesta no es JSON, usamos el mensaje por defecto
        }
        setError(mensajeDeError(datos, 'No se pudo cargar el cliente.'));
      } else {
        alElegir(await respuesta.json());
        setNoEncontrado(false);
        setDni('');
        setNombre('');
        setApellido('');
        setTelefono('');
      }
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setCreando(false);
    }
  }

  function cancelarAlta() {
    setNoEncontrado(false);
    setError('');
    setNombre('');
    setApellido('');
    setTelefono('');
  }

  if (cliente) {
    return (
      <p>
        Cliente: <strong>{cliente.apellido}, {cliente.nombre}</strong> (DNI {cliente.dni}){' '}
        <button type="button" onClick={() => alElegir(null)}>
          Cambiar
        </button>
      </p>
    );
  }

  return (
    <div style={{ marginBottom: '12px' }}>
      <div>
        <label>
          DNI del cliente:{' '}
          <input
            value={dni}
            onChange={(e) => {
              setDni(e.target.value);
              setNoEncontrado(false);
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') buscar();
            }}
            placeholder="7 u 8 números"
            disabled={noEncontrado}
          />
        </label>{' '}
        <button type="button" onClick={buscar} disabled={buscando || noEncontrado}>
          {buscando ? 'Buscando...' : 'Buscar'}
        </button>
      </div>

      {noEncontrado && (
        <div style={{ marginTop: '8px' }}>
          <p>No hay un cliente con el DNI {dniLimpio}. Cargalo:</p>
          <div>
            <label>
              Nombre:{' '}
              <input value={nombre} onChange={(e) => setNombre(e.target.value)} />
            </label>
          </div>
          <div>
            <label>
              Apellido:{' '}
              <input value={apellido} onChange={(e) => setApellido(e.target.value)} />
            </label>
          </div>
          <div>
            <label>
              Teléfono (opcional):{' '}
              <input value={telefono} onChange={(e) => setTelefono(e.target.value)} />
            </label>
          </div>
          <button type="button" onClick={crear} disabled={creando}>
            {creando ? 'Guardando...' : 'Guardar cliente'}
          </button>{' '}
          <button type="button" onClick={cancelarAlta} disabled={creando}>
            Cancelar
          </button>
        </div>
      )}

      {error && <p style={{ color: 'crimson' }}>{error}</p>}
    </div>
  );
}