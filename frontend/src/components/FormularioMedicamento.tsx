import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { API_URL } from '../config/api';
import { NuevoCatalogo } from './NuevoCatalogo';

interface Opcion {
  id: number;
  nombre: string;
}

export interface DatosMedicamento {
  producto_id: number;
  principio_activo_id: number;
  concentracion: string;
  forma_farmaceutica_id: number;
  requiere_receta: boolean;
  categoria_cobertura_obra_social_id: number | null;
  clases_terapeuticas_ids: number[];
}

interface Props {
  productoId: number;
  productoNombre: string;
  token: string;
  actual: DatosMedicamento | null; // null = alta, con datos = edición
  onGuardado: () => void;
  onCancelar: () => void;
}

function mensajeDeError(datos: unknown, porDefecto: string): string {
  const detalle = (datos as { detail?: unknown })?.detail;
  if (typeof detalle === 'string') return detalle;
  if (Array.isArray(detalle) && detalle.length > 0) {
    return String((detalle[0] as { msg?: string }).msg ?? porDefecto);
  }
  return porDefecto;
}

export function FormularioMedicamento({
  productoId,
  productoNombre,
  token,
  actual,
  onGuardado,
  onCancelar,
}: Props) {
  const [principios, setPrincipios] = useState<Opcion[]>([]);
  const [formas, setFormas] = useState<Opcion[]>([]);
  const [categorias, setCategorias] = useState<Opcion[]>([]);
  const [clases, setClases] = useState<Opcion[]>([]);
  const [cargandoCatalogos, setCargandoCatalogos] = useState(true);

  const [principioId, setPrincipioId] = useState(actual ? String(actual.principio_activo_id) : '');
  const [concentracion, setConcentracion] = useState(actual?.concentracion ?? '');
  const [formaId, setFormaId] = useState(actual ? String(actual.forma_farmaceutica_id) : '');
  const [requiereReceta, setRequiereReceta] = useState(actual?.requiere_receta ?? false);
  const [categoriaId, setCategoriaId] = useState(
    actual?.categoria_cobertura_obra_social_id ? String(actual.categoria_cobertura_obra_social_id) : ''
  );
  const [clasesIds, setClasesIds] = useState<number[]>(actual?.clases_terapeuticas_ids ?? []);

  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function cargarCatalogos() {
      try {
        const cabeceras = { Authorization: `Bearer ${token}` };
        const pedir = (ruta: string) => fetch(`${API_URL}/catalogos/${ruta}`, { headers: cabeceras });
        const [rp, rf, rc, rt] = await Promise.all([
          pedir('principios-activos'),
          pedir('formas-farmaceuticas'),
          pedir('categorias-cobertura'),
          pedir('clases-terapeuticas'),
        ]);
        if (!rp.ok || !rf.ok || !rc.ok || !rt.ok) {
          setError('No se pudieron cargar los catálogos.');
          return;
        }
        const [dp, df, dc, dt] = await Promise.all([rp.json(), rf.json(), rc.json(), rt.json()]);
        setPrincipios(dp.map((x: any) => ({ id: x.id_principio_activo, nombre: x.nombre })));
        setFormas(df.map((x: any) => ({ id: x.id_forma_farmaceutica, nombre: x.nombre })));
        setCategorias(dc.map((x: any) => ({ id: x.id_categoria_cobertura_obra_social, nombre: x.nombre })));
        setClases(dt.map((x: any) => ({ id: x.id_clase_terapeutica, nombre: x.nombre })));
      } catch {
        setError('No se pudo conectar con el servidor. Revisá tu conexión.');
      } finally {
        setCargandoCatalogos(false);
      }
    }
    cargarCatalogos();
  }, [token]);

  function alternarClase(id: number) {
    setClasesIds((previas) => (previas.includes(id) ? previas.filter((c) => c !== id) : [...previas, id]));
  }

  async function guardar(e: FormEvent) {
    e.preventDefault();
    setError('');
    if (!principioId || !formaId || !concentracion.trim()) {
      setError('Completá principio activo, concentración y forma farmacéutica.');
      return;
    }
    setGuardando(true);
    try {
      const cuerpo = {
        principio_activo_id: Number(principioId),
        concentracion: concentracion.trim(),
        forma_farmaceutica_id: Number(formaId),
        requiere_receta: requiereReceta,
        categoria_cobertura_obra_social_id: categoriaId ? Number(categoriaId) : null,
        clases_terapeuticas_ids: clasesIds,
      };
      const respuesta = await fetch(`${API_URL}/productos/${productoId}/medicamento`, {
        method: actual ? 'PATCH' : 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(cuerpo),
      });
      if (respuesta.status === 401) {
        setError('Tu sesión venció. Volvé a iniciar sesión.');
        return;
      }
      if (respuesta.status === 403) {
        setError('No tenés permiso para hacer esta acción.');
        return;
      }
      if (!respuesta.ok) {
        const datos = await respuesta.json().catch(() => ({}));
        setError(mensajeDeError(datos, 'No se pudieron guardar los datos del medicamento.'));
        return;
      }
      onGuardado();
    } catch {
      setError('No se pudo conectar con el servidor. Revisá tu conexión.');
    } finally {
      setGuardando(false);
    }
  }

  const campo = { display: 'block', marginBottom: '12px' } as const;
  const entrada = { display: 'block', width: '100%', padding: '6px', marginTop: '4px' } as const;

  return (
    <form onSubmit={guardar} style={{ border: '1px solid #ccc', padding: '16px', marginTop: '16px' }}>
      <h3 style={{ marginTop: 0 }}>
        {actual ? 'Editar' : 'Cargar'} datos de medicamento: {productoNombre}
      </h3>

      {cargandoCatalogos ? (
        <p>Cargando catálogos...</p>
      ) : (
        <>
          <div style={campo}>
            <label style={{ display: 'block' }}>
              Principio activo
              <select value={principioId} onChange={(e) => setPrincipioId(e.target.value)} style={entrada}>
                <option value="">Elegí uno</option>
                {principios.map((p) => (
                  <option key={p.id} value={p.id}>{p.nombre}</option>
                ))}
              </select>
            </label>
            <NuevoCatalogo
              token={token}
              ruta="principios-activos"
              campoId="id_principio_activo"
              etiqueta="principio activo"
              alCrear={(nuevo) => {
                setPrincipios((previos) =>
                  [...previos, { id: nuevo.id, nombre: nuevo.nombre }].sort((a, b) =>
                    a.nombre.localeCompare(b.nombre)
                  )
                );
                setPrincipioId(String(nuevo.id));
              }}
            />
          </div>

          <label style={campo}>
            Concentración
            <input
              type="text"
              value={concentracion}
              onChange={(e) => setConcentracion(e.target.value)}
              placeholder="Ej: 400 mg"
              style={entrada}
            />
          </label>

          <label style={campo}>
            Forma farmacéutica
            <select value={formaId} onChange={(e) => setFormaId(e.target.value)} style={entrada}>
              <option value="">Elegí una</option>
              {formas.map((f) => (
                <option key={f.id} value={f.id}>{f.nombre}</option>
              ))}
            </select>
          </label>

          <label style={campo}>
            <input
              type="checkbox"
              checked={requiereReceta}
              onChange={(e) => setRequiereReceta(e.target.checked)}
            />{' '}
            Requiere receta
          </label>

          <label style={campo}>
            Categoría de cobertura (opcional)
            <select value={categoriaId} onChange={(e) => setCategoriaId(e.target.value)} style={entrada}>
              <option value="">Sin categoría</option>
              {categorias.map((c) => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </label>

          <fieldset style={{ marginBottom: '12px' }}>
            <legend>Clases terapéuticas (opcional)</legend>
            {clases.map((c) => (
              <label key={c.id} style={{ display: 'block' }}>
                <input
                  type="checkbox"
                  checked={clasesIds.includes(c.id)}
                  onChange={() => alternarClase(c.id)}
                />{' '}
                {c.nombre}
              </label>
            ))}
          </fieldset>
        </>
      )}

      {error && <p style={{ color: 'crimson' }}>{error}</p>}

      <button type="submit" disabled={guardando || cargandoCatalogos}>
        {guardando ? 'Guardando...' : 'Guardar'}
      </button>{' '}
      <button type="button" onClick={onCancelar} disabled={guardando}>
        Cancelar
      </button>
    </form>
  );
}