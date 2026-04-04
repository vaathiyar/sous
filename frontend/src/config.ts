const API_BASE = import.meta.env.VITE_BACKEND_API_URL;
if (!API_BASE) throw new Error('VITE_BACKEND_API_URL is not set');

export { API_BASE };
