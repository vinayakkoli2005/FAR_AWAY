// Client-side SGP4 (satellite.js) -> Cesium SampledPositionProperty.
// All heavy math is server-side; the client only animates (plan Section 11).

import * as satellite from "satellite.js";

export interface SampledTrack {
  times: Date[];
  /** ECEF positions in meters, aligned with `times`; null where propagation failed */
  positions: ({ x: number; y: number; z: number } | null)[];
}

export function satrecFromTle(line1: string, line2: string): satellite.SatRec | null {
  try {
    const rec = satellite.twoline2satrec(line1, line2);
    return rec;
  } catch {
    return null;
  }
}

/** Sample ECEF positions every stepS seconds across [start, start+durationS]. */
export function sampleTrack(
  rec: satellite.SatRec,
  start: Date,
  durationS: number,
  stepS: number
): SampledTrack {
  const times: Date[] = [];
  const positions: SampledTrack["positions"] = [];
  for (let t = 0; t <= durationS; t += stepS) {
    const when = new Date(start.getTime() + t * 1000);
    times.push(when);
    const pv = satellite.propagate(rec, when);
    if (!pv?.position || typeof pv.position === "boolean") {
      positions.push(null);
      continue;
    }
    const gmst = satellite.gstime(when);
    const ecf = satellite.eciToEcf(pv.position, gmst);
    positions.push({ x: ecf.x * 1000, y: ecf.y * 1000, z: ecf.z * 1000 });
  }
  return { times, positions };
}

export const VERDICT_COLORS: Record<string, string> = {
  DODGE: "#ff4d4d",
  WATCH: "#ffb347",
  WAIT: "#3ddc84",
};
