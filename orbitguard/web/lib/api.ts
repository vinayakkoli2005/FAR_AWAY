// Typed client for the OrbitGuard API (the frozen OpenAPI contract).

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface MissRIC {
  radial: number;
  in_track: number;
  cross_track: number;
}

export interface Probability {
  pc: number | null;
  pc_max: number | null;
  method: string;
  chan_crosscheck: number | null;
  hard_body_radius_m: number;
  hbr_source?: string;
  ellipse?: { sigma_major_m: number; sigma_minor_m: number; theta_deg: number } | null;
}

export interface PartyInfo {
  norad_id: number;
  name: string;
  gp_epoch_utc: string;
  gp_age_hours: number;
  object_type?: string;
}

export interface Evidence {
  event_id: string;
  verdict: "DODGE" | "WATCH" | "WAIT";
  escalate: boolean;
  data_grade: string;
  simulated?: boolean;
  asset: PartyInfo;
  object: PartyInfo;
  tca_utc: string;
  miss_distance_km: number;
  miss_ric_km: MissRIC;
  relative_velocity_kms: number;
  probability: Probability;
  policy: { rationale: string; low_vrel_flag: boolean; thresholds: Record<string, number> };
  screening: { distance_km: number; window_days: number; coarse_step_s: number };
  limits: string;
}

export interface Funnel {
  catalog_size: number;
  stage_a_survivors: number;
  stage_a_per_asset: Record<string, number>;
  stage_b_windows: number;
  stage_c_events: number;
  runtime_s: Record<string, number>;
}

export interface ConjunctionsResponse {
  generated_utc: string;
  source: string;
  window_days: number;
  asset_ids: number[];
  funnel: Funnel;
  events: Evidence[];
}

export interface CatalogEntry {
  norad_id: number;
  name: string;
  object_type: string;
  perigee_km: number;
  apogee_km: number;
  inclination_deg: number;
  epoch_utc: string;
  omm: Record<string, unknown>;
  tle: [string, string] | null;
}

export interface Explanation {
  event_id: string;
  text: string;
  source: string;
  model: string | null;
}

// Static mode: a serverless deployment (Vercel) ships the physics engine's
// output as frozen JSON under /data — no Python backend required. The bake
// command (`orbitguard bake`) produces those files.
export const STATIC_MODE = process.env.NEXT_PUBLIC_STATIC === "1";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path}: ${res.status} ${await res.text()}`);
  return res.json();
}

async function getStatic<T>(file: string): Promise<T> {
  const res = await fetch(`/data/${file}`);
  if (!res.ok) throw new Error(`/data/${file}: ${res.status}`);
  return res.json();
}

let conjCache: ConjunctionsResponse | null = null;
async function staticConjunctions(): Promise<ConjunctionsResponse> {
  if (!conjCache) conjCache = await getStatic<ConjunctionsResponse>("conjunctions.json");
  return conjCache;
}

export const fetchConjunctions = (assets?: string, days = 7) =>
  STATIC_MODE
    ? staticConjunctions()
    : get<ConjunctionsResponse>(
        `/conjunctions?days=${days}${assets ? `&assets=${assets}` : ""}`
      );

export const fetchEvent = async (id: string): Promise<Evidence> => {
  if (STATIC_MODE) {
    const c = await staticConjunctions();
    const ev = c.events.find((e) => e.event_id === id);
    if (!ev) throw new Error(`unknown event ${id}`);
    return ev;
  }
  return get<Evidence>(`/conjunction/${id}`);
};

export const fetchExplanation = async (id: string): Promise<Explanation> => {
  if (STATIC_MODE) {
    const all = await getStatic<Record<string, Omit<Explanation, "event_id">>>(
      "explanations.json"
    );
    const x = all[id];
    return { event_id: id, text: x?.text ?? "", source: x?.source ?? "template", model: x?.model ?? null };
  }
  return get<Explanation>(`/explain/${id}`);
};

export const fetchCatalog = (limit = 1200, ids?: string) =>
  STATIC_MODE
    ? getStatic<CatalogEntry[]>("catalog.json")
    : get<CatalogEntry[]>(`/catalog?limit=${limit}${ids ? `&ids=${ids}` : ""}`);

export const fetchScorecard = () =>
  STATIC_MODE
    ? getStatic<Record<string, unknown>>("scorecard.json")
    : get<Record<string, unknown>>(`/scorecard`);
