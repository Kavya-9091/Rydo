import { Loader2, MapPin } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { searchLocations, type Coordinates } from "../../features/rides/geocoding";

interface LocationSearchInputProps {
  value: string;
  placeholder?: string;
  iconClassName?: string;
  rightAction?: React.ReactNode;
  onChange: (value: string) => void;
  onSelect: (location: Coordinates) => void;
}

export function LocationSearchInput({
  value,
  placeholder,
  iconClassName = "text-slate-950",
  rightAction,
  onChange,
  onSelect,
}: LocationSearchInputProps) {
  const [suggestions, setSuggestions] = useState<Coordinates[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const handle = window.setTimeout(() => {
      if (value.trim().length < 3) {
        setSuggestions([]);
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      searchLocations(value, 6)
        .then((results) => {
          if (!controller.signal.aborted) {
            setSuggestions(results);
            setIsOpen(true);
          }
        })
        .catch(() => {
          if (!controller.signal.aborted) {
            setSuggestions([]);
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) {
            setIsLoading(false);
          }
        });
    }, 350);

    return () => {
      controller.abort();
      window.clearTimeout(handle);
    };
  }, [value]);

  useEffect(() => {
    function closeOnOutsideClick(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", closeOnOutsideClick);
    return () => document.removeEventListener("mousedown", closeOnOutsideClick);
  }, []);

  return (
    <div ref={containerRef} className="relative">
      <div className="flex min-h-14 items-center gap-3 rounded-md border border-slate-200 bg-white px-3 transition focus-within:border-slate-950 focus-within:ring-2 focus-within:ring-slate-950/10">
        <MapPin size={18} className={`shrink-0 ${iconClassName}`} />
        <input
          value={value}
          onChange={(event) => {
            onChange(event.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          aria-label={placeholder ?? "Location"}
          className="h-14 min-w-0 flex-1 bg-transparent text-sm text-slate-950 outline-none placeholder:text-transparent"
        />
        {isLoading && <Loader2 size={16} className="shrink-0 animate-spin text-slate-400" />}
        {rightAction}
      </div>

      {isOpen && suggestions.length > 0 && (
        <div className="absolute left-0 right-0 top-[calc(100%+6px)] z-30 max-h-72 overflow-auto rounded-md border border-slate-200 bg-white py-1 shadow-panel">
          {suggestions.map((location) => (
            <button
              key={`${location.latitude}-${location.longitude}-${location.displayName}`}
              type="button"
              onClick={() => {
                onSelect(location);
                setIsOpen(false);
              }}
              className="flex w-full gap-3 px-3 py-3 text-left text-sm hover:bg-slate-50"
            >
              <MapPin size={16} className="mt-0.5 shrink-0 text-slate-400" />
              <span className="line-clamp-2 text-slate-700">{location.displayName}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
