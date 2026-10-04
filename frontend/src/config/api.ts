// Dirección del backend. Un solo lugar para cambiarla cuando se despliegue en la nube.
// Si existe la variable VITE_API_URL (archivo .env del frontend) se usa esa,
// si no, se usa localhost.
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';