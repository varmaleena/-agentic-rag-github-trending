const apiUrl = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;

export function apiEndpoint(path) {
  return new URL(path, apiUrl);
}

export function websocketEndpoint(path) {
  const url = apiEndpoint(path);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  return url;
}
