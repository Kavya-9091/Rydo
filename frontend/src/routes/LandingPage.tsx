import { Car, Crosshair, Loader2, MapPin, Share2, Square, UserRound } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { LocationSearchInput } from "../components/rides/LocationSearchInput";
import { reverseGeocode } from "../features/rides/geocoding";
import { usePageTitle } from "../lib/usePageTitle";

export function LandingPage() {
  usePageTitle("Home");
  const navigate = useNavigate();
  const [pickup, setPickup] = useState("");
  const [destination, setDestination] = useState("");
  const [isLocating, setIsLocating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function useCurrentLocation() {
    setError(null);
    if (!navigator.geolocation) {
      setError("Location is not supported in this browser.");
      return;
    }

    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const latitude = Number(position.coords.latitude.toFixed(7));
          const longitude = Number(position.coords.longitude.toFixed(7));
          const location = await reverseGeocode(latitude, longitude);
          setPickup(location.displayName);
        } catch (error) {
          setError(error instanceof Error ? error.message : "Type your Bengaluru pickup.");
        } finally {
          setIsLocating(false);
        }
      },
      (locationError) => {
        setError(
          locationError.message === "Rydo is currently available only in Bengaluru."
            ? locationError.message
            : "Allow location access or type your Bengaluru pickup.",
        );
        setIsLocating(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    );
  }

  function seePrices() {
    const params = new URLSearchParams();
    if (pickup) params.set("pickup", pickup);
    if (destination) params.set("destination", destination);
    navigate(`/login${params.toString() ? `?${params.toString()}` : ""}`);
  }

  const mapSource = buildGoogleMapSource(pickup, destination);

  return (
    <main className="min-h-screen bg-white text-slate-950">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
          <Link to="/" className="text-3xl font-semibold tracking-tight">
            Rydo
          </Link>
          <nav className="hidden h-full items-center gap-6 sm:flex">
            <Link to="/" className="flex h-full items-center gap-2 border-b-4 border-black px-3 text-sm font-semibold">
              <Car size={18} />
              Ride
            </Link>
            <Link to="/rent" className="flex h-full items-center gap-2 px-3 text-sm font-semibold text-slate-700">
              <MapPin size={18} />
              Rent
            </Link>
          </nav>
          <nav className="flex items-center gap-2">
            <button type="button" className="hidden size-9 items-center justify-center rounded-full hover:bg-slate-100 sm:flex" aria-label="Share">
              <Share2 size={18} />
            </button>
            <Link to="/login" className="rounded-full px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-slate-100">
              Login
            </Link>
            <Link to="/register" className="rounded-full bg-black px-5 py-2 text-sm font-semibold text-white">
              Sign up
            </Link>
          </nav>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl gap-7 px-4 py-8 sm:px-6 lg:grid-cols-[520px_1fr]">
        <div className="rounded-md border border-slate-200 bg-white p-6 shadow-sm">
          <h1 className="text-3xl font-semibold leading-tight">Get a ride</h1>

          <div className="mt-6 space-y-4">
            <LocationSearchInput
              value={pickup}
              placeholder="Pickup location"
              onChange={setPickup}
              onSelect={(location) => setPickup(location.displayName)}
              rightAction={
                <button
                  type="button"
                  onClick={useCurrentLocation}
                  disabled={isLocating}
                  className="flex size-8 shrink-0 items-center justify-center rounded-full hover:bg-slate-100 disabled:opacity-60"
                  aria-label="Use current location"
                >
                  {isLocating ? <Loader2 size={16} className="animate-spin" /> : <Crosshair size={16} />}
                </button>
              }
            />
            <LocationSearchInput
              value={destination}
              placeholder="Where to?"
              iconClassName="text-slate-950"
              onChange={setDestination}
              onSelect={(location) => setDestination(location.displayName)}
              rightAction={<Square size={14} className="shrink-0 fill-black text-black" />}
            />
            <button type="button" className="flex h-14 w-full items-center justify-between rounded-md bg-slate-100 px-4 text-left text-sm font-medium text-slate-950">
              <span className="flex items-center gap-3">
                <span className="flex size-7 items-center justify-center rounded-full bg-black text-white">
                  <UserRound size={16} />
                </span>
                For me
              </span>
              <span>v</span>
            </button>
          </div>
          {error && <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

          <button
            type="button"
            onClick={seePrices}
            className="mt-6 flex h-14 w-full items-center justify-center rounded-md bg-black text-base font-semibold text-white hover:bg-slate-900"
          >
            Search
          </button>
        </div>

        <div className="relative min-h-[520px] overflow-hidden rounded-md bg-slate-100">
          <iframe
            key={mapSource}
            src={mapSource}
            title="Rydo pickup and destination map"
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
            className="absolute inset-0 h-full w-full border-0"
            allowFullScreen
          />
          <button type="button" onClick={useCurrentLocation} className="absolute bottom-6 right-6 z-10 flex size-12 items-center justify-center rounded-full bg-white shadow-panel" aria-label="Current location">
            <Crosshair size={20} />
          </button>
        </div>
      </section>
    </main>
  );
}

function buildGoogleMapSource(pickup: string, destination: string) {
  const trimmedPickup = pickup.trim();
  const trimmedDestination = destination.trim();

  if (trimmedPickup && trimmedDestination) {
    const params = new URLSearchParams({
      output: "embed",
      saddr: trimmedPickup,
      daddr: trimmedDestination,
    });
    return `https://www.google.com/maps?${params.toString()}`;
  }

  const query = trimmedPickup || trimmedDestination || "Bengaluru, Karnataka, India";
  const params = new URLSearchParams({
    q: query,
    z: "12",
    output: "embed",
  });
  return `https://www.google.com/maps?${params.toString()}`;
}
