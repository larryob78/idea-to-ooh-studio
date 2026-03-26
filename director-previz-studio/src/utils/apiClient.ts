import axios from 'axios';

const jsonHeaders = { 'Content-Type': 'application/json' };

export const meshyClient = axios.create({
  baseURL: 'https://api.meshy.ai',
  headers: jsonHeaders,
});

export const trellisClient = axios.create({
  baseURL: 'https://api.trellis3d.ai',
  headers: jsonHeaders,
});

export const worldLabsClient = axios.create({
  baseURL: 'https://api.worldlabs.ai',
  headers: jsonHeaders,
});

export const nvidiaClient = axios.create({
  baseURL: 'https://integrate.api.nvidia.com',
  headers: jsonHeaders,
});

meshyClient.interceptors.request.use((config) => {
  const key = import.meta.env.VITE_MESHY_API_KEY;
  if (key) config.headers.Authorization = `Bearer ${key}`;
  return config;
});

trellisClient.interceptors.request.use((config) => {
  const key = import.meta.env.VITE_TRELLIS_API_KEY;
  if (key) config.headers.Authorization = `Bearer ${key}`;
  return config;
});

worldLabsClient.interceptors.request.use((config) => {
  const key = import.meta.env.VITE_WORLDLABS_API_KEY;
  if (key) config.headers.Authorization = `Bearer ${key}`;
  return config;
});

nvidiaClient.interceptors.request.use((config) => {
  const key = import.meta.env.VITE_NVIDIA_API_KEY;
  if (key) config.headers.Authorization = `Bearer ${key}`;
  return config;
});
