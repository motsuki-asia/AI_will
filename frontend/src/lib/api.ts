/**
 * API Client for AI will Backend
 */

const API_BASE_URL = '/v1';

// Token storage
let accessToken: string | null = localStorage.getItem('access_token');
let refreshToken: string | null = localStorage.getItem('refresh_token');

export function setTokens(access: string, refresh: string) {
  accessToken = access;
  refreshToken = refresh;
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

export function getAccessToken() {
  return accessToken;
}

// Fetch wrapper with auth
async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // Handle 401 - try refresh
  if (response.status === 401 && refreshToken) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      headers['Authorization'] = `Bearer ${accessToken}`;
      return fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
      });
    }
  }

  return response;
}

async function refreshAccessToken(): Promise<boolean> {
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (response.ok) {
      const data = await response.json();
      setTokens(data.tokens.access_token, data.tokens.refresh_token);
      return true;
    }
  } catch {
    // Refresh failed
  }

  clearTokens();
  return false;
}

// =============================================================================
// Auth API
// =============================================================================

export async function register(email: string, password: string) {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || 'Registration failed');
  }

  const data = await response.json();
  setTokens(data.tokens.access_token, data.tokens.refresh_token);
  return data;
}

export async function login(email: string, password: string) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || 'Login failed');
  }

  const data = await response.json();
  setTokens(data.tokens.access_token, data.tokens.refresh_token);
  return data;
}

export async function logout() {
  try {
    await fetchWithAuth('/auth/logout', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  } finally {
    clearTokens();
  }
}

export async function getMe() {
  const response = await fetchWithAuth('/me');
  if (!response.ok) {
    if (response.status === 401) {
      clearTokens();
      throw new Error('Unauthenticated');
    }
    throw new Error('Failed to get user info');
  }
  return response.json();
}

export async function consent(termsVersion: string, privacyVersion: string) {
  const response = await fetchWithAuth('/me/consent', {
    method: 'POST',
    body: JSON.stringify({ terms_version: termsVersion, privacy_version: privacyVersion }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || 'Consent failed');
  }

  return response.json();
}

export async function ageVerify(ageGroup: 'u13' | 'u18' | 'adult') {
  const response = await fetchWithAuth('/me/age-verify', {
    method: 'POST',
    body: JSON.stringify({ age_group: ageGroup }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || 'Age verification failed');
  }

  return response.json();
}

// =============================================================================
// Catalog API
// =============================================================================

export async function getPacks(params?: { type?: string; query?: string }) {
  const searchParams = new URLSearchParams();
  if (params?.type) searchParams.set('type', params.type);
  if (params?.query) searchParams.set('query', params.query);

  const queryString = searchParams.toString();
  const response = await fetchWithAuth(`/packs${queryString ? `?${queryString}` : ''}`);

  if (!response.ok) {
    throw new Error('Failed to get packs');
  }

  return response.json();
}

export async function getPack(packId: string) {
  const response = await fetchWithAuth(`/packs/${packId}`);

  if (!response.ok) {
    throw new Error('Failed to get pack');
  }

  return response.json();
}

export async function getPackItems(packId: string) {
  const response = await fetchWithAuth(`/packs/${packId}/items`);

  if (!response.ok) {
    throw new Error('Failed to get pack items');
  }

  return response.json();
}

export async function getCharacters(params?: { query?: string }) {
  const searchParams = new URLSearchParams();
  if (params?.query) searchParams.set('query', params.query);

  const queryString = searchParams.toString();
  const response = await fetchWithAuth(`/characters${queryString ? `?${queryString}` : ''}`);

  if (!response.ok) {
    throw new Error('Failed to get characters');
  }

  return response.json();
}

// =============================================================================
// Conversation API
// =============================================================================

export async function getThreads() {
  const response = await fetchWithAuth('/threads');

  if (!response.ok) {
    throw new Error('Failed to get threads');
  }

  return response.json();
}

export async function createThread(packId: string | null, characterId: string) {
  const body: { pack_id?: string; character_id: string } = { character_id: characterId };
  if (packId) {
    body.pack_id = packId;
  }

  const response = await fetchWithAuth('/threads', {
    method: 'POST',
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || 'Failed to create thread');
  }

  return response.json();
}

export async function getThread(threadId: string) {
  const response = await fetchWithAuth(`/threads/${threadId}`);

  if (!response.ok) {
    throw new Error('Failed to get thread');
  }

  return response.json();
}

export async function getMessages(threadId: string, order: 'asc' | 'desc' = 'asc') {
  const response = await fetchWithAuth(`/threads/${threadId}/messages?order=${order}`);

  if (!response.ok) {
    throw new Error('Failed to get messages');
  }

  return response.json();
}

export async function sendMessage(threadId: string, content: string) {
  const response = await fetchWithAuth(`/threads/${threadId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || 'Failed to send message');
  }

  return response.json();
}

export async function deleteThread(threadId: string) {
  const response = await fetchWithAuth(`/threads/${threadId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete thread');
  }
}

// =============================================================================
// TTS (Text-to-Speech) API
// =============================================================================

export async function getMessageAudio(threadId: string, messageId: string, voice: string = 'nova'): Promise<Blob> {
  const headers: Record<string, string> = {};
  
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  const response = await fetch(
    `${API_BASE_URL}/threads/${threadId}/messages/${messageId}/audio?voice=${voice}`,
    { headers }
  );

  if (!response.ok) {
    throw new Error('Failed to get message audio');
  }

  return response.blob();
}

// =============================================================================
// Image Generation API
// =============================================================================

export interface GenerateImageParams {
  name: string;
  description?: string;
  style?: 'anime' | 'realistic' | 'illustration';
}

export interface GenerateImageResponse {
  face_image_url: string;
  full_body_image_url: string;
  style: string;
}

export interface ImageStyle {
  id: string;
  name: string;
  description: string;
}

export async function generateImage(params: GenerateImageParams): Promise<GenerateImageResponse> {
  const response = await fetchWithAuth('/images/generate', {
    method: 'POST',
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || 'Failed to generate image');
  }

  return response.json();
}

export async function getImageStyles(): Promise<{ styles: ImageStyle[] }> {
  const response = await fetchWithAuth('/images/styles');

  if (!response.ok) {
    throw new Error('Failed to get image styles');
  }

  return response.json();
}

// =============================================================================
// Partner Creation API
// =============================================================================

export type VoiceId = 'nova' | 'shimmer' | 'alloy' | 'echo' | 'fable' | 'onyx';

export interface CreatePartnerParams {
  name: string;
  description?: string;
  image_url: string;
  full_body_image_url?: string;
  voice_id: VoiceId;
}

export interface CreatePartnerResponse {
  character_id: string;
  thread_id: string;
  name: string;
  image_url: string;
  full_body_image_url?: string;
  voice_id: string;
}

export async function createPartner(params: CreatePartnerParams): Promise<CreatePartnerResponse> {
  const response = await fetchWithAuth('/images/partner', {
    method: 'POST',
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || 'Failed to create partner');
  }

  return response.json();
}

export async function getVoiceSample(voiceId: VoiceId): Promise<Blob> {
  const headers: Record<string, string> = {};
  
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${API_BASE_URL}/images/voice-sample/${voiceId}`, {
    headers,
  });

  if (!response.ok) {
    throw new Error('Failed to get voice sample');
  }

  return response.blob();
}
