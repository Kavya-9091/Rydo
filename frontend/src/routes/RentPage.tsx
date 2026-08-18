import { usePageTitle } from "../lib/usePageTitle";

export function RentPage() {
  usePageTitle("Rent a Vehicle");

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold">Rent a Vehicle</h1>
      <p className="mt-4 text-lg">This feature is coming soon!</p>
    </div>
  );
}
