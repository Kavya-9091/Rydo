import { Bike, Car, Crown, Shield, Truck, UsersRound } from "lucide-react";

import type { VehicleType } from "../../types/ride";

const VEHICLE_META: Record<VehicleType, { label: string; helper: string; icon: React.ReactNode }> = {
  bike: { label: "Bike", helper: "Fast solo trips", icon: <Bike size={20} /> },
  auto: { label: "Auto", helper: "Short city hops", icon: <Shield size={20} /> },
  mini: { label: "Mini", helper: "Everyday rides", icon: <Car size={20} /> },
  sedan: { label: "Sedan", helper: "Comfort commute", icon: <UsersRound size={20} /> },
  suv: { label: "SUV", helper: "More room", icon: <Truck size={20} /> },
  luxury: { label: "Luxury", helper: "Premium ride", icon: <Crown size={20} /> },
};

interface VehicleOptionProps {
  type: VehicleType;
  selected: boolean;
  onSelect: (type: VehicleType) => void;
}

export function VehicleOption({ type, selected, onSelect }: VehicleOptionProps) {
  const meta = VEHICLE_META[type];

  return (
    <button
      type="button"
      onClick={() => onSelect(type)}
      className={`flex min-h-[76px] items-center gap-3 rounded-md border p-3 text-left transition ${
        selected
          ? "border-slate-950 bg-slate-950 text-white"
          : "border-slate-200 bg-white text-slate-950 hover:border-slate-400"
      }`}
    >
      <span
        className={`flex size-10 shrink-0 items-center justify-center rounded-md ${
        selected ? "bg-white/15 text-white" : "bg-slate-100 text-slate-600"
        }`}
      >
        {meta.icon}
      </span>
      <span>
        <span className="block text-sm font-semibold">{meta.label}</span>
        <span className={`block text-xs ${selected ? "text-slate-300" : "text-slate-500"}`}>
          {meta.helper}
        </span>
      </span>
    </button>
  );
}
