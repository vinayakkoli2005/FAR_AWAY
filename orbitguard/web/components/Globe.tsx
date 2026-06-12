"use client";

// The OrbitGuard globe. Two modes:
//  - Mission Control: whole-sky view; every dot (asset, conjunction partner,
//    or ambient catalog object) is hoverable, clickable and followable.
//  - Encounter simulation (inspector): the clock jumps to TCA-15 min, both
//    objects fly their real trajectories, the camera tracks your asset and a
//    live separation readout counts down to closest approach.
//
// Offline-first: NaturalEarthII imagery ships with Cesium's static assets,
// so no ion token or network is required (plan R7).

import { useEffect, useRef, useState } from "react";
import type { CatalogEntry, Evidence } from "@/lib/api";
import { sampleTrack, satrecFromTle, VERDICT_COLORS } from "@/lib/orbits";

// Cesium is deliberately NOT bundled: webpack mangles its prebuilt modules
// (octal-escape parse errors). We load the static build we already copy to
// /public/cesium — the officially supported standalone integration.
let cesiumPromise: Promise<any> | null = null;
function loadCesium(): Promise<any> {
  if ((window as any).Cesium) return Promise.resolve((window as any).Cesium);
  if (!cesiumPromise) {
    (window as any).CESIUM_BASE_URL = "/cesium";
    cesiumPromise = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = "/cesium/Cesium.js";
      s.onload = () => resolve((window as any).Cesium);
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }
  return cesiumPromise;
}

export interface EncounterSpec {
  tcaIso: string;
  assetId: number;
  objectId: number;
  missKm: number;
}

interface GlobeProps {
  catalog: CatalogEntry[];
  events: Evidence[];
  assetIds: number[];
  focusEventId?: string;
  encounter?: EncounterSpec;
}

interface SelInfo {
  entry: CatalogEntry;
  isAsset: boolean;
  following: boolean;
}

export default function Globe({
  catalog, events, assetIds, focusEventId, encounter,
}: GlobeProps) {
  const ref = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);
  const hoverRef = useRef<HTMLDivElement>(null);
  const sepRef = useRef<HTMLDivElement>(null);
  const [selected, setSelected] = useState<SelInfo | null>(null);
  // ambient catalog layer: context in mission control, noise in the
  // encounter view — so it defaults off there and is always toggleable
  const [showAmbient, setShowAmbient] = useState(!encounter);
  const [camMode, setCamMode] = useState<"cine" | "chase" | "free">("cine");
  const [speed, setSpeed] = useState(25);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    let destroyed = false;

    (async () => {
      const Cesium = await loadCesium();
      if (destroyed || !ref.current) return;

      const imagery = await Cesium.TileMapServiceImageryProvider.fromUrl(
        Cesium.buildModuleUrl("Assets/Textures/NaturalEarthII")
      );
      const viewer = new Cesium.Viewer(ref.current, {
        baseLayer: new Cesium.ImageryLayer(imagery),
        baseLayerPicker: false,
        geocoder: false,
        homeButton: false,
        sceneModePicker: false,
        navigationHelpButton: false,
        infoBox: false,
        selectionIndicator: false,
        timeline: true,
        animation: true,
        shouldAnimate: true,
      });
      viewerRef.current = viewer;
      viewer.scene.globe.enableLighting = true;

      const byId = new Map(catalog.map((c) => [c.norad_id, c]));
      const assetSet = new Set(assetIds);

      // ---- clock window: whole-sky now+3h, or the encounter window ----
      const tca = encounter ? new Date(encounter.tcaIso) : null;
      const start = tca
        ? new Date(tca.getTime() - 15 * 60 * 1000)
        : new Date();
      const horizonS = tca ? 35 * 60 : 3 * 3600;
      const startJd = Cesium.JulianDate.fromDate(start);
      const stopJd = Cesium.JulianDate.addSeconds(startJd, horizonS, new Cesium.JulianDate());
      viewer.clock.startTime = startJd;
      viewer.clock.stopTime = stopJd;
      viewer.clock.currentTime = startJd;
      viewer.clock.clockRange = Cesium.ClockRange.LOOP_STOP;
      viewer.clock.multiplier = tca ? 25 : 30;
      viewer.timeline.zoomTo(startJd, stopJd);

      // top events drive which partners get full animated treatment
      const ranked = [...events].sort(
        (a, b) =>
          (b.probability.pc ?? b.probability.pc_max ?? 0) -
          (a.probability.pc ?? a.probability.pc_max ?? 0)
      );
      const topEvents = ranked.slice(0, 12);
      const partnerVerdict = new Map<number, string>();
      for (const e of topEvents) {
        const prev = partnerVerdict.get(e.object.norad_id);
        if (!prev || e.verdict === "DODGE" || (e.verdict === "WATCH" && prev === "WAIT")) {
          partnerVerdict.set(e.object.norad_id, e.verdict);
        }
      }
      if (encounter) partnerVerdict.set(encounter.objectId, "WATCH");

      const makeSampled = (entry: CatalogEntry, stepS: number) => {
        if (!entry.tle) return null;
        const rec = satrecFromTle(entry.tle[0], entry.tle[1]);
        if (!rec) return null;
        const track = sampleTrack(rec, start, horizonS, stepS);
        const prop = new Cesium.SampledPositionProperty(Cesium.ReferenceFrame.FIXED);
        prop.setInterpolationOptions({
          interpolationDegree: 5,
          interpolationAlgorithm: Cesium.LagrangePolynomialApproximation,
        });
        track.times.forEach((t, i) => {
          const p = track.positions[i];
          if (p) {
            prop.addSample(Cesium.JulianDate.fromDate(t), new Cesium.Cartesian3(p.x, p.y, p.z));
          }
        });
        return prop;
      };

      const encounterPair = encounter
        ? new Set([encounter.assetId, encounter.objectId])
        : null;
      const ambient: any[] = [];

      for (const entry of catalog) {
        const isAsset = assetSet.has(entry.norad_id);
        const verdict = partnerVerdict.get(entry.norad_id);
        const inPair = encounterPair?.has(entry.norad_id) ?? false;

        if (isAsset || verdict || inPair) {
          // fine sampling for encounter pair so the flyby is glass-smooth
          const prop = makeSampled(entry, encounter && inPair ? 5 : 20);
          if (!prop) continue;
          const color = isAsset
            ? Cesium.Color.fromCssColorString("#43d2ff")
            : Cesium.Color.fromCssColorString(VERDICT_COLORS[verdict ?? "WATCH"] ?? "#ffb347");
          // encounter pair gets comet-style glow trails (trail only, so the
          // direction of motion is unambiguous); mission control keeps the
          // full lead+trail orbit line, partners shorter than assets
          const path = encounter && inPair
            ? new Cesium.PathGraphics({
                leadTime: 0,
                trailTime: 1500,
                width: isAsset ? 3.2 : 2.6,
                resolution: 5,
                material: new Cesium.PolylineGlowMaterialProperty({
                  glowPower: 0.22,
                  taperPower: 0.55,
                  color: color.withAlpha(0.9),
                }),
              })
            : new Cesium.PathGraphics({
                leadTime: isAsset ? 2700 : 1200,
                trailTime: isAsset ? 2700 : 1200,
                width: isAsset ? 1.8 : 1.2,
                // resolution makes orbit lines curve smoothly instead of
                // looking like chained straight segments (default is 60 s)
                resolution: 12,
                material: new Cesium.ColorMaterialProperty(color.withAlpha(isAsset ? 0.7 : 0.45)),
              });
          const ent = viewer.entities.add({
            id: `sat-${entry.norad_id}`,
            name: entry.name,
            position: prop,
            point: { pixelSize: isAsset ? 9 : 7, color, outlineColor: Cesium.Color.BLACK, outlineWidth: 1 },
            label: {
              text: entry.name,
              font: "11px SF Mono, Menlo, monospace",
              fillColor: color,
              pixelOffset: new Cesium.Cartesian2(10, -10),
              showBackground: true,
              backgroundColor: Cesium.Color.fromCssColorString("#0b1426").withAlpha(0.7),
            },
            path,
          });
          // steady over-the-shoulder camera when this entity is tracked
          ent.viewFrom = new Cesium.Cartesian3(-180e3, -180e3, 90e3);
        } else {
          // ambient background: real tracked objects, hover/click to identify
          const prop = makeSampled(entry, 120);
          if (!prop) continue;
          const ent = viewer.entities.add({
            id: `sat-${entry.norad_id}`,
            name: entry.name,
            show: !encounter,
            position: prop,
            point: {
              pixelSize: 2.2,
              color: Cesium.Color.fromCssColorString("#7d92bb").withAlpha(0.75),
            },
          });
          ent.viewFrom = new Cesium.Cartesian3(-180e3, -180e3, 90e3);
          ambient.push(ent);
        }
      }

      // conjunction markers at TCA positions; labels only for the top risks
      const labelled = new Set(topEvents.map((e) => e.event_id));
      for (const e of events) {
        const entry = byId.get(e.object.norad_id) ?? byId.get(e.asset.norad_id);
        if (!entry?.tle) continue;
        const rec = satrecFromTle(entry.tle[0], entry.tle[1]);
        if (!rec) continue;
        const when = new Date(e.tca_utc);
        const t = sampleTrack(rec, when, 0, 1);
        const p = t.positions[0];
        if (!p) continue;
        const showLabel = labelled.has(e.event_id) || Boolean(focusEventId);
        viewer.entities.add({
          id: `evt-${e.event_id}`,
          name: `${e.verdict}: ${e.asset.name} x ${e.object.name}`,
          position: new Cesium.Cartesian3(p.x, p.y, p.z),
          point: {
            pixelSize: showLabel ? 12 : 7,
            color: Cesium.Color.fromCssColorString(VERDICT_COLORS[e.verdict]).withAlpha(0.25),
            outlineColor: Cesium.Color.fromCssColorString(VERDICT_COLORS[e.verdict]),
            outlineWidth: showLabel ? 2 : 1.2,
          },
          label: showLabel
            ? {
                text: `${e.verdict}${e.simulated ? " (SIM)" : ""} · ${e.miss_distance_km.toFixed(2)} km`,
                font: "10px SF Mono, Menlo, monospace",
                fillColor: Cesium.Color.fromCssColorString(VERDICT_COLORS[e.verdict]),
                pixelOffset: new Cesium.Cartesian2(12, 0),
                showBackground: true,
                backgroundColor: Cesium.Color.fromCssColorString("#0b1426").withAlpha(0.8),
              }
            : undefined,
        });
      }

      // ---- encounter mode: cinematic dual-tracking + tether + telemetry ----
      if (encounter && tca) {
        const aEnt = viewer.entities.getById(`sat-${encounter.assetId}`);
        const bEnt = viewer.entities.getById(`sat-${encounter.objectId}`);
        const tcaJd = Cesium.JulianDate.fromDate(tca);
        const scratchA = new Cesium.Cartesian3();
        const scratchB = new Cesium.Cartesian3();
        const pairAt = (time: any) => {
          const pa = aEnt?.position?.getValue(time, scratchA);
          const pb = bEnt?.position?.getValue(time, scratchB);
          return pa && pb ? [pa, pb] : null;
        };
        const sepColor = (km: number) =>
          km < 50 ? "#ff4d4d" : km < 500 ? "#ffb347" : "#3ddc84";

        // tether: a dashed line between the two objects, recolored live by
        // separation — the literal visualization of "how close are they now"
        if (aEnt && bEnt) {
          viewer.entities.add({
            polyline: {
              positions: new Cesium.CallbackProperty((time: any) => {
                const p = pairAt(time);
                return p ? [p[0].clone(), p[1].clone()] : [];
              }, false),
              width: 1.8,
              material: new Cesium.PolylineDashMaterialProperty({
                dashLength: 14,
                color: new Cesium.CallbackProperty((time: any) => {
                  const p = pairAt(time);
                  if (!p) return Cesium.Color.TRANSPARENT;
                  const km = Cesium.Cartesian3.distance(p[0], p[1]) / 1000;
                  return Cesium.Color.fromCssColorString(sepColor(km)).withAlpha(0.85);
                }, false),
              }),
            },
          });
          // floating range tag at the midpoint of the tether
          const PosProp = Cesium.CallbackPositionProperty ?? Cesium.CallbackProperty;
          viewer.entities.add({
            position: new PosProp((time: any) => {
              const p = pairAt(time);
              return p
                ? Cesium.Cartesian3.midpoint(p[0], p[1], new Cesium.Cartesian3())
                : undefined;
            }, false),
            label: {
              text: new Cesium.CallbackProperty((time: any) => {
                const p = pairAt(time);
                if (!p) return "";
                const km = Cesium.Cartesian3.distance(p[0], p[1]) / 1000;
                return km >= 100 ? `${km.toFixed(0)} km` : `${km.toFixed(2)} km`;
              }, false),
              font: "12px SF Mono, Menlo, monospace",
              fillColor: new Cesium.CallbackProperty((time: any) => {
                const p = pairAt(time);
                if (!p) return Cesium.Color.WHITE;
                const km = Cesium.Cartesian3.distance(p[0], p[1]) / 1000;
                return Cesium.Color.fromCssColorString(sepColor(km));
              }, false),
              showBackground: true,
              backgroundColor: Cesium.Color.fromCssColorString("#0b1426").withAlpha(0.85),
              pixelOffset: new Cesium.Cartesian2(0, -16),
            },
          });
        }

        // TCA pulse: the closest-approach marker breathes during the final
        // and first 90 simulated seconds around the event
        const focusEvt = focusEventId
          ? viewer.entities.getById(`evt-${focusEventId}`)
          : null;
        if (focusEvt?.point) {
          focusEvt.point.pixelSize = new Cesium.CallbackProperty((time: any) => {
            const dt = Math.abs(Cesium.JulianDate.secondsDifference(tcaJd, time));
            return dt < 90 ? 14 + 7 * Math.abs(Math.sin(dt / 6)) : 12;
          }, false);
        }

        // cinematic camera: frames BOTH objects, zooming as they converge
        let camMode = "cine";
        let smoothRange = 0;
        (viewer as any).__setCamMode = (m: string) => {
          camMode = m;
          if (m === "chase" && aEnt) {
            viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY);
            viewer.trackedEntity = aEnt;
          } else {
            viewer.trackedEntity = undefined;
            if (m === "free") viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY);
          }
        };
        viewer.scene.preRender.addEventListener(() => {
          if (camMode !== "cine") return;
          const p = pairAt(viewer.clock.currentTime);
          if (!p) return;
          const mid = Cesium.Cartesian3.midpoint(p[0], p[1], new Cesium.Cartesian3());
          const sep = Cesium.Cartesian3.distance(p[0], p[1]);
          const target = Math.min(Math.max(sep * 2.4, 90e3), 5.5e6);
          smoothRange = smoothRange === 0 ? target : smoothRange + (target - smoothRange) * 0.06;
          viewer.camera.lookAt(mid, new Cesium.HeadingPitchRange(0.45, -0.32, smoothRange));
        });

        // live telemetry strip
        viewer.clock.onTick.addEventListener((clock: any) => {
          if (!sepRef.current) return;
          const dt = Cesium.JulianDate.secondsDifference(tcaJd, clock.currentTime);
          let sep = "";
          const p = pairAt(clock.currentTime);
          if (p) {
            const km = Cesium.Cartesian3.distance(p[0], p[1]) / 1000;
            sep = `<span style="color:${sepColor(km)}">separation ${
              km >= 100 ? km.toFixed(0) : km.toFixed(2)
            } km</span>`;
          }
          const sign = dt >= 0 ? "T−" : "T+";
          const a = Math.abs(dt);
          const mm = Math.floor(a / 60), ss = Math.floor(a % 60);
          sepRef.current.innerHTML =
            `${sep}${sep ? " · " : ""}${sign}${mm}m ${ss}s to closest approach`;
        });
      }

      // ---- picking: hover names + click to select/follow ----
      const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
      let lastHover = 0;
      handler.setInputAction((m: any) => {
        const now = performance.now();
        if (now - lastHover < 60) return;
        lastHover = now;
        const div = hoverRef.current;
        if (!div) return;
        const picked = viewer.scene.pick(m.endPosition);
        const name = picked?.id?.name;
        if (name) {
          div.textContent = name;
          div.style.display = "block";
          div.style.left = `${m.endPosition.x + 14}px`;
          div.style.top = `${m.endPosition.y + 8}px`;
        } else {
          div.style.display = "none";
        }
      }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

      handler.setInputAction((c: any) => {
        const picked = viewer.scene.pick(c.position);
        const id: string | undefined = picked?.id?.id;
        if (id?.startsWith("sat-")) {
          const norad = Number(id.slice(4));
          const entry = byId.get(norad);
          if (entry) {
            setSelected({
              entry,
              isAsset: assetSet.has(norad),
              following: viewer.trackedEntity === picked.id,
            });
            return;
          }
        }
        if (id?.startsWith("evt-")) {
          window.location.href = `/event/${id.slice(4)}`;
          return;
        }
        setSelected(null);
      }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
      (viewer as any).__ogHandler = handler;

      // initial camera
      const focus = focusEventId
        ? viewer.entities.getById(`evt-${focusEventId}`)
        : viewer.entities.getById(`sat-${assetIds[0]}`);
      if (focus && !encounter) {
        const range = focusEventId ? 2.0e6 : 1.1e7;
        viewer.flyTo(focus, { offset: new Cesium.HeadingPitchRange(0, -0.7, range) });
      }

      // locate buttons on event cards fly the camera to that encounter
      const onFocus = (e: Event) => {
        const id = (e as CustomEvent).detail as string;
        const ent = viewer.entities.getById(`evt-${id}`);
        if (ent) {
          viewer.trackedEntity = undefined;
          viewer.flyTo(ent, { offset: new Cesium.HeadingPitchRange(0, -0.6, 2.5e6) });
        }
      };
      window.addEventListener("og-focus", onFocus);
      (viewer as any).__ogFocusListener = onFocus;
      (viewer as any).__ogAmbient = ambient;

      // following an ambient object: its 120 s samples are fine for a dot but
      // wobble under a tracking camera — resample at 10 s before locking on
      (viewer as any).__ogResample = (norad: number) => {
        const entry = byId.get(norad);
        const ent = viewer.entities.getById(`sat-${norad}`);
        if (!entry || !ent || ent.__fine) return ent;
        const prop = makeSampled(entry, 10);
        if (prop) {
          ent.position = prop;
          ent.__fine = true;
        }
        return ent;
      };
    })();

    return () => {
      destroyed = true;
      const v = viewerRef.current;
      if (v?.__ogFocusListener) window.removeEventListener("og-focus", v.__ogFocusListener);
      v?.__ogHandler?.destroy?.();
      v?.destroy?.();
      viewerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [catalog, events]);

  const follow = () => {
    const viewer = viewerRef.current;
    if (!viewer || !selected) return;
    const Cesium = (window as any).Cesium;
    if (selected.following) {
      viewer.trackedEntity = undefined;
      setSelected({ ...selected, following: false });
      return;
    }
    // smooth tracking needs fine position samples + a stable view offset
    const ent = viewer.__ogResample?.(selected.entry.norad_id)
      ?? viewer.entities.getById(`sat-${selected.entry.norad_id}`);
    if (!ent) return;
    if (!ent.path) {
      ent.path = new Cesium.PathGraphics({
        leadTime: 2700, trailTime: 2700, width: 1.4, resolution: 12,
        material: new Cesium.ColorMaterialProperty(
          Cesium.Color.fromCssColorString("#9db4dd").withAlpha(0.7)
        ),
      });
    }
    ent.viewFrom = new Cesium.Cartesian3(-180e3, -180e3, 90e3);
    viewer.trackedEntity = ent;
    setSelected({ ...selected, following: true });
  };

  const toggleAmbient = () => {
    const viewer = viewerRef.current;
    const next = !showAmbient;
    viewer?.__ogAmbient?.forEach((e: any) => (e.show = next));
    setShowAmbient(next);
  };

  const switchCam = (m: "cine" | "chase" | "free") => {
    viewerRef.current?.__setCamMode?.(m);
    setCamMode(m);
  };
  const setClockSpeed = (x: number) => {
    if (viewerRef.current) viewerRef.current.clock.multiplier = x;
    setSpeed(x);
  };
  const togglePause = () => {
    const v = viewerRef.current;
    if (!v) return;
    v.clock.shouldAnimate = paused;
    setPaused(!paused);
  };
  const restart = () => {
    const v = viewerRef.current;
    if (!v) return;
    v.clock.currentTime = v.clock.startTime.clone();
    v.clock.shouldAnimate = true;
    setPaused(false);
  };

  const sel = selected?.entry;
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <div ref={ref} style={{ position: "absolute", inset: 0 }} />
      <div ref={hoverRef} className="hover-tip" />
      {encounter && <div ref={sepRef} className="sep-readout" />}
      {encounter && (
        <div className="enc-controls">
          <span className="ctl-group">
            <button className={camMode === "cine" ? "on" : ""} onClick={() => switchCam("cine")}
              title="Auto-frame both objects, zooming as they converge">🎬 cinematic</button>
            <button className={camMode === "chase" ? "on" : ""} onClick={() => switchCam("chase")}
              title="Ride along behind your satellite">🛰 chase</button>
            <button className={camMode === "free" ? "on" : ""} onClick={() => switchCam("free")}
              title="Free orbit camera — drag to look around">🖱 free</button>
          </span>
          <span className="ctl-group">
            <button onClick={restart} title="Back to T−15 min">⏮</button>
            <button onClick={togglePause}>{paused ? "▶" : "⏸"}</button>
            {[1, 25, 60, 120].map((x) => (
              <button key={x} className={speed === x ? "on" : ""} onClick={() => setClockSpeed(x)}>
                {x}×
              </button>
            ))}
          </span>
        </div>
      )}
      <button
        className={`layer-toggle tip ${showAmbient ? "on" : ""}`}
        data-tip="The grey dots are the rest of the tracked catalog — real Starlinks, debris and rocket bodies for situational context. Toggle them off to focus on your assets."
        onClick={toggleAmbient}
      >
        ⬡ catalog {showAmbient ? "ON" : "OFF"}
      </button>
      {sel && (
        <div className="sat-panel">
          <div className="sat-head">
            <b>{sel.name}</b>
            <button className="sat-close" onClick={() => setSelected(null)}>✕</button>
          </div>
          <div className="sat-rows">
            <span>NORAD</span><b>{sel.norad_id}</b>
            <span>Type</span><b>{sel.object_type || (selected!.isAsset ? "YOUR ASSET" : "tracked object")}</b>
            <span>Perigee</span><b>{(sel.perigee_km - 6378).toFixed(0)} km alt</b>
            <span>Apogee</span><b>{(sel.apogee_km - 6378).toFixed(0)} km alt</b>
            <span>Inclination</span><b>{sel.inclination_deg.toFixed(1)}°</b>
            <span>Orbit data</span><b>{new Date(sel.epoch_utc).toISOString().slice(0, 16)}Z</b>
          </div>
          <button className="cta sat-follow" onClick={follow}>
            {selected!.following ? "■ Stop following" : "▶ Follow this object"}
          </button>
        </div>
      )}
    </div>
  );
}
