/**
 * API Client for Lakers in 5 FastAPI Serving Layer
 */

const DEFAULT_API_URL = import.meta.env.VITE_API_URL || "https://lakers-in-5.onrender.com";

export function getStoredApiUrl() {
  return localStorage.getItem("lakers_api_url") || DEFAULT_API_URL;
}

export function setStoredApiUrl(url) {
  if (!url) {
    localStorage.removeItem("lakers_api_url");
  } else {
    localStorage.setItem("lakers_api_url", url.replace(/\/$/, ""));
  }
}

async function request(path, options = {}) {
  const baseUrl = getStoredApiUrl();
  const url = `${baseUrl}${path.startsWith('/') ? path : `/${path}`}`;
  
  const headers = {
    "Accept": "application/json",
    ...(options.headers || {})
  };

  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(options.body);
  }

  const response = await fetch(url, { ...options, headers });
  
  if (!response.ok) {
    const errorText = await response.text();
    let errorDetail = `HTTP ${response.status}`;
    try {
      const parsed = JSON.parse(errorText);
      if (parsed.detail) errorDetail = parsed.detail;
    } catch {
      if (errorText) errorDetail = errorText;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  checkHealth: async () => {
    return request("/health");
  },

  getLakersNext: async () => {
    return request("/predict/lakers/next");
  },

  predictMatchup: async (homeTeam, awayTeam, gameDate, persist = false) => {
    return request("/predict", {
      method: "POST",
      body: {
        home_team: homeTeam,
        away_team: awayTeam,
        game_date: gameDate,
        persist: persist
      }
    });
  },

  getSchedule: async (season = "2026-27", team = "LAL", limit = 10) => {
    const params = new URLSearchParams();
    if (team) params.append("team", team);
    if (limit) params.append("limit", limit.toString());
    return request(`/schedule/${season}?${params.toString()}`);
  },

  getMonitoringHealth: async (window = "30d") => {
    return request(`/monitoring/health?window=${window}`);
  },

  getDriftReport: async () => {
    return request("/monitoring/drift");
  },

  getRetrainingDecision: async () => {
    return request("/monitoring/retrain-decision");
  }
};
