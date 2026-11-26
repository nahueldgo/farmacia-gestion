import { useCallback, useEffect, useState } from 'react';
import { API_URL } from '../config/api';

interface Categoria {
  id: number;
  nombre: string;
}

interface Props {
  token: string;
  obraSocial: { id_obra_social: number; nombre: string };
  alCerrar: () => void;
}

const ETIQUETAS: Record<string, string> = {
  ambulatorio: 'Ambulatorio',
  cronico: 'Crónico',
  diabetes_insulina: 'Diabetes e insulina',
  oncologico: 'Oncológico',
  anticonceptivos: 'Anticonceptivos',
  hiv: 'HIV',
  discapacidad: 'Discapacidad',
};

function etiquetaCategoria(nombre: string) {
  return ETIQUETAS[nombre] ?? nombre.replace(/_/g, ' ');
}

export function PanelReglas({ token, obraSocial, alCerrar }: Props) {
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [valores, setValores] = useState<Record<number, string>>({});
  const [guardados, setGuardados] = useState<Record<number, number>>({});
  const [valorTodas, setValorTodas] = useState('');

  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState('');
  const [mensaje, setMensaje] = useState('');

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const cabeceras = { Authorization: `Bearer ${token}` };
      const [respCat, respReglas] = await Promise.all([
        fetch(`${API_URL}/catalogos/categorias-cobertura`, { headers: cabeceras }),
        fetch(`${API_URL}/obras-sociales/${obraSocial.id_obra_social}/reglas`, { headers: cabeceras }),
      ]);
      if (respCat.status === 401 || respReglas.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
      } else if (!respCat.ok || !respReglas.ok) {
        setError('No se pudieron cargar las reglas de cobertura.');
      } else {
        const datosCat = await respCat.json();
        const datosReglas = await respReglas.json();
        const lista: Categoria[] = datosCat.map(
          (c: { id_categoria_cobertura_obra_social: number; nombre: string }) => ({
            id: c.id_categoria_cobertura_obra_social,
            nombre: c.nombre,
          })
        );
        // Una categoría sin regla se muestra en 0 (no cubre nada)
        const porcentajes: Record<number, number> = {};
        for (const c of lista) porcentajes[c.id] = 0;
        for (const r of datosReglas) {
          porcentajes[r.categoria_cobertura_obra_social_id] = Number(r.porcentaje_cobertura);
        }
        const textos: Record<number, string> = {};
        for (const c of lista) textos[c.id] = String(porcentajes[c.id]);
        setCategorias(lista);
        setGuardados(porcentajes);
        setValores(textos);
        setError('');
      }
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setCargando(false);
    }
  }, [token, obraSocial.id_obra_social]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  function aplicarATodas() {
    setMensaje('');
    const numero = Number(valorTodas);
    if (valorTodas === '' || Number.isNaN(numero) || numero < 0 || numero > 100) {
      setError('El porcentaje para todas tiene que ser un número de 0 a 100.');
      return;
    }
    setError('');
    const nuevos: Record<number, string> = {};
    for (const c of categorias) nuevos[c.id] = valorTodas;
    setValores(nuevos);
  }

  async function guardar() {
    setError('');
    setMensaje('');

    // Validamos todo antes de mandar nada y juntamos solo lo que cambió
    const cambios: { categoria: Categoria; porcentaje: number }[] = [];
    for (const c of categorias) {
      const texto = (valores[c.id] ?? '').trim();
      const numero = texto === '' ? 0 : Number(texto);
      const decimales = texto.includes('.') ? texto.split('.')[1].length : 0;
      if (Number.isNaN(numero) || numero < 0 || numero > 100 || decimales > 2) {
        setError(`${etiquetaCategoria(c.nombre)}: el porcentaje tiene que ir de 0 a 100, con hasta 2 decimales.`);
        return;
      }
      if (numero !== (guardados[c.id] ?? 0)) cambios.push({ categoria: c, porcentaje: numero });
    }
    if (cambios.length === 0) {
      setError('No cambiaste ningún porcentaje.');
      return;
    }

    setGuardando(true);
    try {
      for (const cambio of cambios) {
        const respuesta = await fetch(
          `${API_URL}/obras-sociales/${obraSocial.id_obra_social}/reglas/${cambio.categoria.id}`,
          {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ porcentaje_cobertura: cambio.porcentaje }),
          }
        );
        if (!respuesta.ok) {
          let mensajeError = `No se pudo guardar ${etiquetaCategoria(cambio.categoria.nombre)}.`;
          if (respuesta.status === 401) mensajeError = 'Tu sesión venció. Volvé a iniciar sesión.';
          else if (respuesta.status === 403) mensajeError = 'No tenés permiso para configurar coberturas.';
          else {
            try {
              const datos = await respuesta.json();
              if (typeof datos.detail === 'string') mensajeError = datos.detail;
              else if (Array.isArray(datos.detail) && datos.detail[0]?.msg) mensajeError = datos.detail[0].msg;
            } catch {
              // si la respuesta no es JSON, dejamos el mensaje por defecto
            }
          }
          setError(mensajeError);
          // Lo que sí alcanzó a guardarse se vuelve a leer del servidor
          await cargar();
          return;
        }
      }
      await cargar();
      setMensaje('Reglas guardadas.');
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setGuardando(false);
    }
  }

  return (
    <div style={{ border: '1px solid #ccc', padding: '16px', marginTop: '16px' }}>
      <h3 style={{ marginTop: 0 }}>Reglas de cobertura de {obraSocial.nombre}</h3>
      <p>
        Porcentaje del precio que cubre la obra social en cada categoría de medicamento. Una
        categoría en 0 no tiene cobertura: el cliente paga el precio completo.
      </p>

      {cargando ? (
        <p>Cargando reglas...</p>
      ) : (
        <>
          <p>
            <label>
              Mismo valor para todas:{' '}
              <input
                type="number"
                min="0"
                max="100"
                step="0.01"
                value={valorTodas}
                onChange={(e) => setValorTodas(e.target.value)}
                style={{ width: 80 }}
              />{' '}
              %
            </label>{' '}
            <button onClick={aplicarATodas} disabled={guardando}>
              Aplicar a todas
            </button>
          </p>

          <table>
            <thead>
              <tr>
                <th>Categoría</th>
                <th>Cobertura (%)</th>
              </tr>
            </thead>
            <tbody>
              {categorias.map((c) => (
                <tr key={c.id}>
                  <td>{etiquetaCategoria(c.nombre)}</td>
                  <td>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.01"
                      value={valores[c.id] ?? ''}
                      onChange={(e) => {
                        setMensaje('');
                        setValores({ ...valores, [c.id]: e.target.value });
                      }}
                      style={{ width: 80 }}
                      disabled={guardando}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      {mensaje && <p style={{ color: 'green' }}>{mensaje}</p>}

      <p>
        <button onClick={guardar} disabled={cargando || guardando}>
          {guardando ? 'Guardando...' : 'Guardar reglas'}
        </button>{' '}
        <button onClick={alCerrar} disabled={guardando}>
          Cerrar
        </button>
      </p>
    </div>
  );
}