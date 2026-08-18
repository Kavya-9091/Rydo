import { Crosshair, ExternalLink } from "lucide-react";

import type { Coordinates } from "../../features/rides/geocoding";

type MapMode = "pickup" | "destination";

interface BookingMapSelectorProps {
  pickup: Coordinates | null;
  destination: Coordinates | null;
  mode: MapMode;
  onModeChange: (mode: MapMode) => void;
}

export function BookingMapSelector({
  pickup,
  destination,
  mode,
  onModeChange,
}: BookingMapSelectorProps) {
  const mapSource = buildGoogleMapSource(pickup, destination);
  const fullMapUrl = buildGoogleMapUrl(pickup, destination);

  return (
    <section className="overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-950">Select on map</h2>
          <p className="text-xs text-slate-500">Search pickup and drop above, then review the real route here.</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-full bg-slate-100 p-1">
            <ModeButton active={mode === "pickup"} onClick={() => onModeChange("pickup")} label="Pickup" />
            <ModeButton active={mode === "destination"} onClick={() => onModeChange("destination")} label="Drop" />
          </div>
          <a
            href={fullMapUrl}
            target="_blank"
            rel="noreferrer"
            className="flex size-8 items-center justify-center rounded-md border border-slate-200 text-slate-600 hover:bg-slate-50"
            aria-label="Open full map"
            title="Open full map"
          >
            <ExternalLink size={15} />
          </a>
        </div>
      </div>

      <div className="relative h-[520px] overflow-hidden bg-slate-100">
        <iframe
          key={mapSource}
          src={mapSource}
          title="Rydo booking map"
          loading="lazy"
          referrerPolicy="no-referrer-when-downgrade"
          className="absolute inset-0 h-full w-full border-0"
          allowFullScreen
        />
        <button
          type="button"
          onClick={() => onModeChange(mode === "pickup" ? "destination" : "pickup")}
          className="absolute bottom-5 right-5 z-10 flex size-12 items-center justify-center rounded-full bg-white shadow-panel"
          aria-label="Switch pickup and drop mode"
          title="Switch pickup and drop mode"
        >
          <Crosshair size={20} />
        </button>
      </div>
    </section>
  );
}

function ModeButton({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button type="button" onClick={onClick} className={`rounded-full px-3 py-1 text-xs font-semibold ${active ? "bg-black text-white" : "text-slate-600"}`}>
      {label}
    </button>
  );
}

function buildGoogleMapSource(pickup: Coordinates | null, destination: Coordinates | null) {
  const pickupQuery = pickup?.displayName || coordinatesQuery(pickup);
  const destinationQuery = destination?.displayName || coordinatesQuery(destination);

  if (pickupQuery && destinationQuery) {
    const params = new URLSearchParams({
      output: "embed",
      saddr: pickupQuery,
      daddr: destinationQuery,
    });
    return `https://www.google.com/maps?${params.toString()}`;
  }

  const params = new URLSearchParams({
    q: pickupQuery || destinationQuery || "Bengaluru, Karnataka, India",
    z: "12",
    output: "embed",
  });
  return `https://www.google.com/maps?${params.toString()}`;
}

function buildGoogleMapUrl(pickup: Coordinates | null, destination: Coordinates | null) {
  const pickupQuery = pickup?.displayName || coordinatesQuery(pickup);
  const destinationQuery = destination?.displayName || coordinatesQuery(destination);
  if (pickupQuery && destinationQuery) {
    return `https://www.google.com/maps/dir/?${new URLSearchParams({
      api: "1",
      origin: pickupQuery,
      destination: destinationQuery,
      travelmode: "driving",
    }).toString()}`;
  }
  return `https://www.google.com/maps/search/?${new URLSearchParams({
    api: "1",
    query: pickupQuery || destinationQuery || "Bengaluru, Karnataka, India",
  }).toString()}`;
}

function coordinatesQuery(location: Coordinates | null) {
  return location ? `${location.latitude},${location.longitude}` : "";
}
