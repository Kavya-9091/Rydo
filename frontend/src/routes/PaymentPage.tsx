import { useMutation, useQuery } from "@tanstack/react-query";
import { CreditCard, IndianRupee, Loader2 } from "lucide-react";
import { useState } from "react";

import { MainLayout } from "../components/layout/MainLayout";
import { createPayment, getPaymentHistory, getRideHistory } from "../features/rides/rideApi";
import { usePageTitle } from "../lib/usePageTitle";

export function PaymentPage() {
  usePageTitle("Payment");
  const [method, setMethod] = useState("card");
  const { data } = useQuery({ queryKey: ["ride-history"], queryFn: getRideHistory });
  const payments = useQuery({ queryKey: ["payment-history"], queryFn: getPaymentHistory });
  const paidRideIds = new Set(payments.data?.map((payment) => payment.ride_id) ?? []);
  const payable = data
    ?.filter((ride) => ride.status === "completed" && !paidRideIds.has(ride.id))
    .sort((first, second) => {
      const firstTime = new Date(first.completed_at ?? first.requested_at).getTime();
      const secondTime = new Date(second.completed_at ?? second.requested_at).getTime();
      return secondTime - firstTime;
    })[0];
  const mutation = useMutation({ mutationFn: () => createPayment(payable!.id, method) });

  return (
    <MainLayout>
      <main className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
        <section className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
          <h1 className="text-3xl font-semibold text-slate-950">Payment</h1>
          {!payable ? <p className="mt-4 text-slate-500">No completed unpaid rides available for payment.</p> : (
            <>
              <div className="mt-6 rounded-md bg-slate-50 p-4">
                <p className="text-sm text-slate-500">Selected ride</p>
                <p className="mt-1 break-all font-medium">{payable.id}</p>
                <p className="mt-3 flex items-center text-2xl font-semibold"><IndianRupee />{payable.final_fare ?? payable.estimated_fare ?? 0}</p>
              </div>
              <select value={method} onChange={(e) => setMethod(e.target.value)} className="mt-5 h-12 w-full rounded-md border border-slate-200 px-3">
                <option value="card">Card</option><option value="upi">UPI</option><option value="cash">Cash</option>
              </select>
              <button onClick={() => mutation.mutate()} disabled={mutation.isPending} className="mt-5 flex h-12 w-full items-center justify-center gap-2 rounded-md bg-ink text-sm font-semibold text-white">
                {mutation.isPending ? <Loader2 className="animate-spin" /> : <CreditCard size={18} />} Pay now
              </button>
              {mutation.data && <p className="mt-4 rounded-md bg-slate-100 p-3 text-slate-900">Payment {mutation.data.payment_status}</p>}
              {mutation.error && <p className="mt-4 rounded-md bg-red-50 p-3 text-red-700">{mutation.error.message}</p>}
            </>
          )}
        </section>
      </main>
    </MainLayout>
  );
}
