export interface MovimientoCaja {
  id_movimiento_caja: number;
  tipo: string;
  monto: number;
  motivo: string;
  hora: string;
}

interface Totales {
  cantidad: number;
  total_a_pagar: number;
  monto_cobertura: number;
}

export interface ConsolidadoCaja {
  caja: {
    id_caja: number;
    hora_apertura: string;
    empleado_apertura?: string;
    monto_apertura: number;
    estado: string;
    hora_cierre: string | null;
    monto_cierre_declarado: number | null;
    monto_cierre_sistema: number | null;
    diferencia: number | null;
  };
  ventas: Totales;
  por_tipo: (Totales & { tipo: string })[];
  por_medio_pago: (Totales & { medio_pago: string })[];
  total_ingresos: number;
  total_retiros: number;
  movimientos: MovimientoCaja[];
  efectivo_esperado: number;
}

const ETIQUETAS_TIPO: Record<string, string> = {
  mostrador: 'Mostrador',
  con_cobertura: 'Con cobertura',
};

const ETIQUETAS_MEDIO: Record<string, string> = {
  efectivo: 'Efectivo',
  tarjeta_credito: 'Tarjeta de crédito',
  tarjeta_debito: 'Tarjeta de débito',
  transferencia: 'Transferencia',
  qr: 'QR',
};

function formatearMonto(valor: number) {
  return valor.toLocaleString('es-AR', { style: 'currency', currency: 'ARS' });
}

function formatearFechaHora(iso: string) {
  return new Date(iso).toLocaleString('es-AR', { hourCycle: 'h23' });
}

export function ResumenCaja({ consolidado }: { consolidado: ConsolidadoCaja }) {
  const { caja, ventas } = consolidado;
  const cerrada = caja.estado !== 'abierta';

  return (
    <div>
      <p>
        <strong>{cerrada ? 'Caja cerrada' : 'Caja abierta'}</strong> el{' '}
        {formatearFechaHora(caja.hora_apertura)}
        {cerrada && caja.hora_cierre && <> · cerrada el {formatearFechaHora(caja.hora_cierre)}</>}
        {caja.empleado_apertura && <> · abierta por {caja.empleado_apertura}</>}
      </p>
      <p>Monto inicial: {formatearMonto(caja.monto_apertura)}</p>

      <h3>Ventas de esta caja</h3>
      <p>
        {ventas.cantidad} {ventas.cantidad === 1 ? 'venta' : 'ventas'} · Cobrado en caja:{' '}
        <strong>{formatearMonto(ventas.total_a_pagar)}</strong> · A cargo de obras sociales:{' '}
        {formatearMonto(ventas.monto_cobertura)}
      </p>

      <h4>Por tipo de venta</h4>
      <table>
        <thead>
          <tr>
            <th>Tipo</th>
            <th>Ventas</th>
            <th>Cobrado</th>
            <th>Obra social</th>
          </tr>
        </thead>
        <tbody>
          {consolidado.por_tipo.map((t) => (
            <tr key={t.tipo}>
              <td>{ETIQUETAS_TIPO[t.tipo] ?? t.tipo}</td>
              <td>{t.cantidad}</td>
              <td>{formatearMonto(t.total_a_pagar)}</td>
              <td>{formatearMonto(t.monto_cobertura)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h4>Por medio de pago</h4>
      <table>
        <thead>
          <tr>
            <th>Medio de pago</th>
            <th>Ventas</th>
            <th>Cobrado</th>
          </tr>
        </thead>
        <tbody>
          {consolidado.por_medio_pago.map((m) => (
            <tr key={m.medio_pago}>
              <td>{ETIQUETAS_MEDIO[m.medio_pago] ?? m.medio_pago}</td>
              <td>{m.cantidad}</td>
              <td>{formatearMonto(m.total_a_pagar)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Movimientos manuales</h3>
      {consolidado.movimientos.length === 0 ? (
        <p>No hay ingresos ni retiros.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Hora</th>
              <th>Tipo</th>
              <th>Monto</th>
              <th>Motivo</th>
            </tr>
          </thead>
          <tbody>
            {consolidado.movimientos.map((m) => (
              <tr key={m.id_movimiento_caja}>
                <td>{formatearFechaHora(m.hora)}</td>
                <td>{m.tipo === 'ingreso' ? 'Ingreso' : 'Retiro'}</td>
                <td>{formatearMonto(m.monto)}</td>
                <td>{m.motivo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <p>
        Ingresos: {formatearMonto(consolidado.total_ingresos)} · Retiros:{' '}
        {formatearMonto(consolidado.total_retiros)}
      </p>

      <h3>Efectivo</h3>
      <p>
        Efectivo esperado: <strong>{formatearMonto(consolidado.efectivo_esperado)}</strong>
      </p>
      <p style={{ color: 'gray' }}>
        Monto inicial + cobrado en efectivo + ingresos - retiros.
      </p>

      {cerrada && caja.monto_cierre_declarado !== null && caja.diferencia !== null && (
        <div>
          <h3>Arqueo</h3>
          <p>Declarado: {formatearMonto(caja.monto_cierre_declarado)}</p>
          <p>Esperado por el sistema: {formatearMonto(caja.monto_cierre_sistema ?? 0)}</p>
          <p
            style={{
              color: caja.diferencia === 0 ? 'green' : 'crimson',
              fontWeight: 'bold',
            }}
          >
            {caja.diferencia === 0
              ? 'Sin diferencia'
              : caja.diferencia > 0
                ? `Sobrante: ${formatearMonto(caja.diferencia)}`
                : `Faltante: ${formatearMonto(Math.abs(caja.diferencia))}`}
          </p>
        </div>
      )}
    </div>
  );
}