/**
 * LocalStorage utility functions for session and API key management
 */

import { STORAGE_KEYS } from "./constants";

// ==================== Session Storage ====================

export function getSessionIdFromStorage(): string | null {
  return localStorage.getItem(STORAGE_KEYS.SESSION_ID);
}

export function saveSessionIdToStorage(sessionId: string): void {
  localStorage.setItem(STORAGE_KEYS.SESSION_ID, sessionId);
}

export function clearSessionFromStorage(): void {
  localStorage.removeItem(STORAGE_KEYS.SESSION_ID);
}

// ==================== API Key Storage ====================

/**
 * Save API key to localStorage.
 * Note: This is stored locally and never sent to our backend.
 * The API key is only included in request headers when calling AI endpoints.
 */
export function saveApiKeyToStorage(apiKey: string): void {
  localStorage.setItem(STORAGE_KEYS.API_KEY, apiKey);
}

/**
 * Retrieve API key from localStorage.
 * Returns null if not found.
 */
export function getApiKeyFromStorage(): string | null {
  return localStorage.getItem(STORAGE_KEYS.API_KEY);
}

/**
 * Remove API key from localStorage.
 */
export function clearApiKeyFromStorage(): void {
  localStorage.removeItem(STORAGE_KEYS.API_KEY);
}

/**
 * Clear all stored data (session + API key).
 * Use this for logout or reset functionality.
 */
export function clearAllStorage(): void {
  clearSessionFromStorage();
  clearApiKeyFromStorage();
}
