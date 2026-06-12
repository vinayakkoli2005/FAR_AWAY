"use client";

// Mission Control globe. Offline-first: NaturalEarthII imagery ships with
// Cesium's static assets, so no ion token or network is required (plan R7).
// Assets + conjunction partners get fully animated tracks; the background
// catalog is a decimated ambient point cloud.

import { useEffect, useRef } from "react";
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

interface GlobeProps {
  catalog: CatalogEntry[];
  events: Evidence[];
  assetIds: number[];
  focusEventId?: string;
}

export default function Globe({ catalog, events, assetIds, focusEventId }: GlobeProps) {
  const ref = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<unknown>(null);

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
      viewer.scene.skyAtmosphere && (viewer.scene.skyAtmosphere.show = true);

      const start = new Date();
      const horizonS = 3 * 3600; // 3 h of animated motion
      const startJd = Cesium.JulianDate.fromDate(start);
      const stopJd = Cesium.JulianDate.addSeconds(startJd, horizonS, new Cesium.JulianDate());
      viewer.clock.startTime = startJd;
      viewer.clock.stopTime = stopJd;
      viewer.clock.currentTime = startJd;
      viewer.clock.clockRange = Cesium.ClockRange.LOOP_STOP;
      viewer.clock.multiplier = 30;
      viewer.timeline.zoomTo(startJd, stopJd);

      const assetSet = new Set(assetIds);
      // rank events by headline risk once; the top slice drives which partner
      // satellites get full animated/labelled treatment vs ambient points
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
            prop.addSample(
              Cesium.JulianDate.fromDate(t),
              new Cesium.Cartesian3(p.x, p.y, p.z)
            );
          }
        });
        return prop;
      };

      for (const entry of catalog) {
        const isAsset = assetSet.has(entry.norad_id);
        const verdict = partnerVerdict.get(entry.norad_id);

        if (isAsset || verdict) {
          const prop = makeSampled(entry, 30);
          if (!prop) continue;
          const color = isAsset
            ? Cesium.Color.fromCssColorString("#43d2ff")
            : Cesium.Color.fromCssColorString(VERDICT_COLORS[verdict!] ?? "#ffb347");
          viewer.entities.add({
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
            path: new Cesium.PathGraphics({
              leadTime: 2700,
              trailTime: 2700,
              width: isAsset ? 1.6 : 1.0,
              material: new Cesium.ColorMaterialProperty(color.withAlpha(isAsset ? 0.65 : 0.4)),
            }),
          });
        } else {
          // ambient background: coarse samples, no label, tiny point
          const prop = makeSampled(entry, 120);
          if (!prop) continue;
          viewer.entities.add({
            position: prop,
            point: {
              pixelSize: 1.6,
              color: Cesium.Color.fromCssColorString("#5a6e96").withAlpha(0.65),
            },
          });
        }
      }

      // conjunction markers at TCA positions; labels only for the top risks
      // to keep the view readable when hundreds of events are on screen
      const labelled = new Set(topEvents.map((e) => e.event_id));
      for (const e of events) {
        const entry = catalog.find((c) => c.norad_id === e.object.norad_id);
        if (!entry?.tle) continue;
        const rec = satrecFromTle(entry.tle[0], entry.tle[1]);
        if (!rec) continue;
        const tca = new Date(e.tca_utc);
        const t = sampleTrack(rec, tca, 0, 1);
        const p = t.positions[0];
        if (!p) continue;
        const showLabel = labelled.has(e.event_id) || Boolean(focusEventId);
        viewer.entities.add({
          id: `evt-${e.event_id}`,
          position: new Cesium.Cartesian3(p.x, p.y, p.z),
          point: {
            pixelSize: showLabel ? 12 : 7,
            color: Cesium.Color.fromCssColorString(VERDICT_COLORS[e.verdict]).withAlpha(0.25),
            outlineColor: Cesium.Color.fromCssColorString(VERDICT_COLORS[e.verdict]),
            outlineWidth: showLabel ? 2 : 1.2,
          },
          label: showLabel
            ? {
                text: `${e.verdict} · ${e.miss_distance_km.toFixed(2)} km`,
                font: "10px SF Mono, Menlo, monospace",
                fillColor: Cesium.Color.fromCssColorString(VERDICT_COLORS[e.verdict]),
                pixelOffset: new Cesium.Cartesian2(12, 0),
                showBackground: true,
                backgroundColor: Cesium.Color.fromCssColorString("#0b1426").withAlpha(0.8),
              }
            : undefined,
        });
      }

      const focus = focusEventId
        ? viewer.entities.getById(`evt-${focusEventId}`)
        : viewer.entities.getById(`sat-${assetIds[0]}`);
      if (focus) {
        // inspector: close-in on the encounter; mission control: planetary context
        const range = focusEventId ? 2.0e6 : 1.1e7;
        viewer.flyTo(focus, { offset: new Cesium.HeadingPitchRange(0, -0.7, range) });
      }

      // "locate" buttons on event cards fly the camera to that encounter
      const onFocus = (e: Event) => {
        const id = (e as CustomEvent).detail as string;
        const ent = viewer.entities.getById(`evt-${id}`);
        if (ent) {
          viewer.flyTo(ent, { offset: new Cesium.HeadingPitchRange(0, -0.6, 2.5e6) });
        }
      };
      window.addEventListener("og-focus", onFocus);
      (viewer as any).__ogFocusListener = onFocus;
    })();

    return () => {
      destroyed = true;
      const v = viewerRef.current as any;
      if (v?.__ogFocusListener) {
        window.removeEventListener("og-focus", v.__ogFocusListener);
      }
      v?.destroy?.();
      viewerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [catalog, events]);

  return <div ref={ref} style={{ position: "absolute", inset: 0 }} />;
}
