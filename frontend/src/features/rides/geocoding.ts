export interface Coordinates {
  latitude: number;
  longitude: number;
  displayName: string;
}

interface NominatimSearchResult {
  lat: string;
  lon: string;
  display_name: string;
}

const BENGALURU_VIEWBOX = "77.3910,13.1737,77.8500,12.7342";
const BENGALURU_CENTER = {
  latitude: 12.9716,
  longitude: 77.5946,
};

export async function geocodeAddress(address: string): Promise<Coordinates> {
  const results = await searchLocations(address, 1);
  const first = results[0];
  if (!first) {
    throw new Error(`No location found for "${address}". Try a more specific place.`);
  }
  return first;
}

export async function searchLocations(query: string, limit = 5): Promise<Coordinates[]> {
  if (query.trim().length < 2) {
    return [];
  }

  const localQuery = query.toLowerCase().includes("bengaluru") || query.toLowerCase().includes("bangalore")
    ? query
    : `${query}, Bengaluru, Karnataka, India`;

  const params = new URLSearchParams({
    q: localQuery,
    format: "json",
    limit: String(limit),
    addressdetails: "1",
    countrycodes: "in",
    viewbox: BENGALURU_VIEWBOX,
    bounded: "1",
  });
  const response = await fetch(`https://nominatim.openstreetmap.org/search?${params.toString()}`, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error("Unable to search that location right now.");
  }

  const results = (await response.json()) as NominatimSearchResult[];
  return results
    .map((item) => ({
      latitude: Number(item.lat),
      longitude: Number(item.lon),
      displayName: item.display_name,
    }))
    .filter((item) => isBengaluruArea(item.latitude, item.longitude));
}

export async function reverseGeocode(latitude: number, longitude: number): Promise<Coordinates> {
  if (!isBengaluruArea(latitude, longitude)) {
    throw new Error("Rydo is currently available only in Bengaluru.");
  }

  const params = new URLSearchParams({
    lat: String(latitude),
    lon: String(longitude),
    format: "json",
  });
  const response = await fetch(`https://nominatim.openstreetmap.org/reverse?${params.toString()}`, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error("Unable to resolve your current address.");
  }

  const result = (await response.json()) as { display_name?: string };

  return {
    latitude,
    longitude,
    displayName: result.display_name || "Current location",
  };
}

export function isBengaluruArea(latitude: number, longitude: number): boolean {
  const north = 13.1737;
  const south = 12.7342;
  const west = 77.3910;
  const east = 77.8500;
  return latitude >= south && latitude <= north && longitude >= west && longitude <= east;
}

export { BENGALURU_CENTER };
