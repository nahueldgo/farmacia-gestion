export interface ItemMenu {
  label: string;
  path: string;
}

export const menuPorRol: Record<string, ItemMenu[]> = {
  auxiliar: [
    { label: 'Ventas', path: '/ventas' },
  ],
  farmaceutico: [
    { label: 'Ventas', path: '/ventas' },
    { label: 'Stock', path: '/stock' },
    { label: 'Configurar coberturas', path: '/coberturas' },
    { label: 'Caja', path: '/caja' },
  ],
  'dueño': [
    { label: 'Ventas', path: '/ventas' },
    { label: 'Stock', path: '/stock' },
    { label: 'Caja', path: '/caja' },
    { label: 'Reportes', path: '/reportes' },
  ],
};