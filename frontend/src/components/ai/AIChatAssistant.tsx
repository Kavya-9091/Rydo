import { useMutation, useQuery } from "@tanstack/react-query";
import { Bot, Eraser, Loader2, Maximize2, MessageCircle, Minimize2, Pencil, Send, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { getAIProviderStatus, sendRideAssistantMessage } from "../../features/ai/aiApi";
import { useAuthStore } from "../../features/auth/authStore";
import { distanceKm, estimateFare } from "../../features/rides/farePreview";
import { geocodeAddress, reverseGeocode, type Coordinates } from "../../features/rides/geocoding";
import { bookRide, getRide } from "../../features/rides/rideApi";
import type { VehicleType } from "../../types/ride";
import { ChatMarkdown } from "./ChatMarkdown";

type ChatRole = "assistant" | "user";
type BookingFlowStep = "idle" | "awaiting_pickup" | "awaiting_destination" | "awaiting_vehicle" | "completed";

const vehicleOptions: Array<{ type: VehicleType; label: string; description: string }> = [
  { type: "bike", label: "Bike", description: "Fast solo trips" },
  { type: "auto", label: "Auto", description: "Short city hops" },
  { type: "mini", label: "Mini", description: "Everyday rides" },
  { type: "sedan", label: "Sedan", description: "Comfort commute" },
  { type: "suv", label: "SUV", description: "More room" },
  { type: "luxury", label: "Luxury", description: "Premium ride" },
];

interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
}

interface BookingFlowState {
  step: BookingFlowStep;
  pickup: string;
  destination: string;
  fareOptions: VehicleFareOption[];
  rideId: string | null;
  selectedVehicle: VehicleType | null;
}

interface VehicleFareOption {
  type: VehicleType;
  label: string;
  description: string;
  fare: number | null;
}

export function AIChatAssistant() {
  const user = useAuthStore((state) => state.user);
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [draft, setDraft] = useState("");
  const storageKey = user ? `rydo-ai-chat-history:${user.id}:${user.role}` : null;
  const flowStorageKey = storageKey ? `${storageKey}:booking-flow` : null;
  const userRole = user?.role ?? "";
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [bookingFlow, setBookingFlow] = useState<BookingFlowState>(emptyBookingFlow());
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const providerStatus = useQuery({
    queryKey: ["ai-provider-status"],
    queryFn: getAIProviderStatus,
    enabled: Boolean(user),
    staleTime: 30000,
  });

  const welcomeMessage = useMemo(
    () => `Hi${user?.full_name ? ` ${user.full_name.split(" ")[0]}` : ""}. I can help with rides, fares, trip status, payments, and support.`,
    [user?.full_name],
  );

  const mutation = useMutation({
    mutationFn: async (message: string) =>
      sendRideAssistantMessage(message, await loadAssistantContext(message, messages, userRole)),
    onSuccess: (response) => {
      appendMessage({
        role: "assistant",
        content: response.reply || "I received your request, but I could not generate a reply.",
      });
    },
    onError: (error) => {
      appendMessage({
        role: "assistant",
        content: `I could not reach the assistant right now. ${errorMessage(error)}`,
      });
    },
  });

  useEffect(() => {
    if (storageKey) {
      setMessages(loadMessages(storageKey));
    }
    if (flowStorageKey) {
      setBookingFlow(loadBookingFlow(flowStorageKey));
    }
  }, [flowStorageKey, storageKey]);

  useEffect(() => {
    if (storageKey) {
      localStorage.setItem(storageKey, JSON.stringify(messages));
    }
  }, [messages, storageKey]);

  useEffect(() => {
    if (flowStorageKey) {
      localStorage.setItem(flowStorageKey, JSON.stringify(bookingFlow));
    }
  }, [bookingFlow, flowStorageKey]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, mutation.isPending, isOpen]);

  if (!user) {
    return null;
  }

  function appendMessage(message: Omit<ChatMessage, "id" | "createdAt">) {
    setMessages((current) => [
      ...current,
      {
        ...message,
        id: crypto.randomUUID(),
        createdAt: new Date().toISOString(),
      },
    ]);
  }

  async function sendMessage() {
    const message = draft.trim();
    if (!message || mutation.isPending) {
      return;
    }

    appendMessage({ role: "user", content: message });
    setDraft("");
    if (await handleGuidedBookingMessage(message)) {
      return;
    }
    mutation.mutate(message);
  }

  function clearConversation() {
    setMessages([]);
    setBookingFlow(emptyBookingFlow());
    if (storageKey) {
      localStorage.removeItem(storageKey);
    }
    if (flowStorageKey) {
      localStorage.removeItem(flowStorageKey);
    }
  }

  async function handleGuidedBookingMessage(message: string) {
    if (userRole === "driver" && isVehicleRegistrationIntent(message)) {
      appendMessage({
        role: "assistant",
        content:
          "You can register your vehicle from this Driver Dashboard. In the Register vehicle section, choose vehicle type, make, model, color, enter the registration number and capacity, then submit it for admin approval.",
      });
      return true;
    }

    if (userRole !== "customer") {
      return false;
    }

    if (isBookingIntent(message) && hasRoute(message)) {
      const route = parseRouteMessage(message);
      if (route.pickup && route.destination) {
        const pickup = await resolveGuidedLocation(route.pickup);
        const destination = await resolveGuidedLocation(route.destination);
        await askVehicleChoice(pickup, destination);
        return true;
      }
    }

    if (/^(clear|cancel|start over|new ride)$/i.test(message.trim())) {
      setBookingFlow(emptyBookingFlow());
      appendMessage({ role: "assistant", content: "No problem. Tell me when you want to book a ride." });
      return true;
    }

    if (bookingFlow.step === "completed" && isPaymentIntent(message)) {
      appendMessage({
        role: "assistant",
        content: bookingFlow.rideId
          ? `Your last ride is ready for payment. Open the Payment tab to pay for ride ${bookingFlow.rideId}.`
          : "Your last ride is ready for payment. Open the Payment tab to complete it.",
      });
      return true;
    }

    if (bookingFlow.step === "completed" && /\b(change|switch|choose again|another)\b/i.test(message)) {
      await askVehicleChoice(bookingFlow.pickup, bookingFlow.destination);
      return true;
    }

    if (bookingFlow.step === "awaiting_pickup") {
      const route = parseRouteMessage(message);
      const pickup = await resolveGuidedLocation(route.pickup || message);
      if (route.destination) {
        const destination = await resolveGuidedLocation(route.destination);
        await askVehicleChoice(pickup, destination);
        return true;
      }
      setBookingFlow({ ...emptyBookingFlow(), step: "awaiting_destination", pickup });
      appendMessage({ role: "assistant", content: "Got it. And what is your drop-off location?" });
      return true;
    }

    if (bookingFlow.step === "awaiting_destination") {
      const destination = message;
      await askVehicleChoice(bookingFlow.pickup, destination);
      return true;
    }

    if (bookingFlow.step === "awaiting_vehicle") {
      if (isOutOfBandDuringVehicleChoice(message, bookingFlow.fareOptions)) {
        appendMessage({
          role: "assistant",
          content: "You have a ride selection pending. Reply with an option number, or type `new ride` to start again.",
        });
        return true;
      }
      const selected = selectVehicleOption(message, bookingFlow.fareOptions);
      if (!selected) {
        appendMessage({ role: "assistant", content: "Please choose a ride by number, for example 1 for Bike or 2 for Auto." });
        return true;
      }
      await createChatRide(selected);
      return true;
    }

    if (/^\d+$/.test(message.trim()) && latestAssistantAskedForVehicle(messages)) {
      appendMessage({ role: "assistant", content: "Please type `new ride` and share the route again so I can show the current vehicle options." });
      return true;
    }

    if (bookingFlow.step === "completed" && isBookingIntent(message)) {
      appendMessage({
        role: "assistant",
        content: `I already have your trip from ${bookingFlow.pickup} to ${bookingFlow.destination}. Type "change vehicle" to choose another ride, or "new ride" to start again.`,
      });
      return true;
    }

    if (isBookingIntent(message)) {
      if (!user) {
        appendMessage({ role: "assistant", content: "I can help with that! Please register or log in to continue." });
        return true;
      }
      const route = parseRouteMessage(message);
      if (route.pickup && route.destination) {
        const pickup = await resolveGuidedLocation(route.pickup);
        const destination = await resolveGuidedLocation(route.destination);
        await askVehicleChoice(pickup, destination);
        return true;
      }
      setBookingFlow({ ...emptyBookingFlow(), step: "awaiting_pickup" });
      appendMessage({ role: "assistant", content: "Welcome! Let's get you moving. What is your exact pickup location?" });
      return true;
    }

    return false;
  }

  async function askVehicleChoice(pickup: string, destination: string) {
    const fareOptions = await buildFareOptions(pickup, destination);
    setBookingFlow({ step: "awaiting_vehicle", pickup, destination, fareOptions, rideId: null, selectedVehicle: null });
    appendMessage({
      role: "assistant",
      content: `Which ride would you like?\n\n${fareOptions
        .map((option, index) => `${index + 1}. ${option.label} - ${option.description} - ${option.fare === null ? "fare unavailable" : `INR ${option.fare}`}`)
        .join("\n")}\n\nReply with the option number.`,
    });
  }

  async function createChatRide(selected: VehicleFareOption) {
    try {
      const [pickup, destination] = await Promise.all([geocodeAddress(bookingFlow.pickup), geocodeAddress(bookingFlow.destination)]);
      const ride = await bookRide({
        ride_type: selected.type,
        pickup_address: pickup.displayName,
        pickup_latitude: pickup.latitude,
        pickup_longitude: pickup.longitude,
        dropoff_address: destination.displayName,
        dropoff_latitude: destination.latitude,
        dropoff_longitude: destination.longitude,
        rider_name: null,
        rider_phone_number: null,
      });
      publishChatBooking({ pickup, destination, vehicleType: selected.type });
      appendMessage({
        role: "assistant",
        content: `Your ${selected.label} ride has been requested from ${pickup.displayName} to ${destination.displayName}. ${
          selected.fare === null ? "" : `Estimated fare is INR ${selected.fare}. `
        }Ride ID: ${ride.id}. Waiting for an approved online ${selected.label} driver to accept.\n\nYou can type "change vehicle" before booking a new ride next time.`,
      });
      setBookingFlow({ ...bookingFlow, step: "completed", rideId: ride.id, selectedVehicle: selected.type });
      watchRideAcceptance(ride.id);
    } catch (error) {
      appendMessage({
        role: "assistant",
        content: `I could not create the ride right now. ${errorMessage(error)}`,
      });
    }
  }

  function watchRideAcceptance(rideId: string) {
    let attempts = 0;
    let acceptedNotified = false;
    const intervalId = window.setInterval(async () => {
      attempts += 1;
      if (attempts > 60) {
        window.clearInterval(intervalId);
        return;
      }
      try {
        const ride = await getRide(rideId);
        if (!acceptedNotified && ride.status === "accepted" && ride.driver_details && ride.vehicle_details) {
          appendMessage({
            role: "assistant",
            content: `${ride.driver_details.full_name} accepted your ride. Phone: ${ride.driver_details.phone_number}. Vehicle: ${ride.vehicle_details.color} ${ride.vehicle_details.make} ${ride.vehicle_details.model}, number ${ride.vehicle_details.registration_number}.`,
          });
          acceptedNotified = true;
        }
        if (ride.status === "completed") {
          appendMessage({
            role: "assistant",
            content: `Your ride is completed. Please go to Payment and pay ${ride.currency} ${ride.final_fare ?? ride.estimated_fare ?? ""}.`,
          });
          window.clearInterval(intervalId);
        }
      } catch {
        window.clearInterval(intervalId);
      }
    }, 5000);
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 sm:bottom-6 sm:right-6">
      {isOpen && (
        <section
          className={`mb-3 flex overflow-hidden rounded-md border border-slate-200 bg-white shadow-2xl ${
            isExpanded
              ? "h-[calc(100vh-2rem)] w-[calc(100vw-2rem)] sm:h-[720px] sm:w-[620px]"
              : "h-[560px] w-[calc(100vw-2rem)] sm:w-[420px]"
          }`}
        >
          <div className="flex min-h-0 w-full flex-col">
            <header className="flex items-center justify-between border-b border-slate-200 bg-black px-4 py-3 text-white">
              <div className="flex items-center gap-3">
                <span className="flex size-9 items-center justify-center rounded-md bg-white text-black">
                  <Bot size={19} />
                </span>
                <div>
                  <h2 className="text-sm font-semibold">Rydo Assistant</h2>
                  <p className="text-xs text-white/60">Online ride support</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <IconButton label="Clear conversation" onClick={clearConversation}>
                  <Eraser size={16} />
                </IconButton>
                <IconButton label={isExpanded ? "Minimize" : "Maximize"} onClick={() => setIsExpanded((value) => !value)}>
                  {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                </IconButton>
                <IconButton label="Close" onClick={() => setIsOpen(false)}>
                  <X size={16} />
                </IconButton>
              </div>
            </header>

            <div className="min-h-0 flex-1 overflow-y-auto bg-slate-50 px-4 py-4">
              <MessageBubble role="assistant" content={welcomeMessage} />
              {providerStatus.data && !providerStatus.data.configured && (
                <div className="mb-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                  Live AI is not configured on the running backend. Add the API key to `.env`, restart the backend, then clear this chat.
                </div>
              )}
              {messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  role={message.role}
                  content={message.content}
                  onEdit={
                    message.role === "user"
                      ? () => {
                          setDraft(message.content);
                          setMessages((current) => current.slice(0, current.findIndex((item) => item.id === message.id)));
                          setBookingFlow(emptyBookingFlow());
                          if (flowStorageKey) {
                            localStorage.removeItem(flowStorageKey);
                          }
                        }
                      : undefined
                  }
                />
              ))}
              {mutation.isPending && (
                <div className="mb-3 flex justify-start">
                  <div className="flex items-center gap-2 rounded-md bg-white px-3 py-2 text-sm text-slate-500 shadow-sm">
                    <TypingDots />
                    Thinking
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            <footer className="border-t border-slate-200 bg-white p-3">
              <div className="mb-2 flex items-center justify-between gap-3">
                <p className="text-xs text-slate-500">Rydo Assistant</p>
                <button
                  type="button"
                  onClick={clearConversation}
                  className="flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  <Eraser size={13} />
                  Clear
                </button>
              </div>
              <div className="flex items-end gap-2">
                <textarea
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      sendMessage();
                    }
                  }}
                  rows={1}
                  maxLength={1000}
                  placeholder="Ask Rydo to help with your ride"
                  className="max-h-28 min-h-11 flex-1 resize-none rounded-md border border-slate-200 px-3 py-3 text-sm outline-none focus:border-black focus:ring-2 focus:ring-black/10"
                />
                <button
                  type="button"
                  onClick={sendMessage}
                  disabled={!draft.trim() || mutation.isPending}
                  className="flex size-11 shrink-0 items-center justify-center rounded-md bg-black text-white disabled:cursor-not-allowed disabled:opacity-50"
                  aria-label="Send message"
                >
                  {mutation.isPending ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
                </button>
              </div>
            </footer>
          </div>
        </section>
      )}

      <button
        type="button"
        onClick={() => setIsOpen((value) => !value)}
        className="flex size-14 items-center justify-center rounded-full bg-black text-white shadow-2xl transition hover:scale-105"
        aria-label="Open Rydo Assistant"
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={25} />}
      </button>
    </div>
  );
}

function emptyBookingFlow(): BookingFlowState {
  return { step: "idle", pickup: "", destination: "", fareOptions: [], rideId: null, selectedVehicle: null };
}

function publishChatBooking({
  pickup,
  destination,
  vehicleType,
}: {
  pickup: Coordinates;
  destination: Coordinates;
  vehicleType: VehicleType;
}) {
  const detail = { pickup, destination, vehicleType };
  localStorage.setItem(
    "rydo-booking-context",
    JSON.stringify({
      pickup,
      destination,
      vehicle_type: vehicleType,
    }),
  );
  window.dispatchEvent(new CustomEvent("rydo-chat-booking-created", { detail }));
}

function loadBookingFlow(storageKey: string): BookingFlowState {
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) {
      return emptyBookingFlow();
    }
    const parsed = JSON.parse(raw) as BookingFlowState;
    if (!parsed || typeof parsed.step !== "string") {
      return emptyBookingFlow();
    }
    return {
      step: parsed.step,
      pickup: parsed.pickup || "",
      destination: parsed.destination || "",
      fareOptions: Array.isArray(parsed.fareOptions) ? parsed.fareOptions : [],
      rideId: typeof parsed.rideId === "string" ? parsed.rideId : null,
      selectedVehicle: typeof parsed.selectedVehicle === "string" ? (parsed.selectedVehicle as VehicleType) : null,
    };
  } catch {
    return emptyBookingFlow();
  }
}

async function buildFareOptions(pickup: string, destination: string): Promise<VehicleFareOption[]> {
  let pickupCoordinates: Coordinates;
  let destinationCoordinates: Coordinates;
  try {
    [pickupCoordinates, destinationCoordinates] = await Promise.all([geocodeAddress(pickup), geocodeAddress(destination)]);
  } catch {
    return vehicleOptions.map((option) => ({ ...option, fare: null }));
  }

  const distance = distanceKm(
    pickupCoordinates.latitude,
    pickupCoordinates.longitude,
    destinationCoordinates.latitude,
    destinationCoordinates.longitude,
  );
  return vehicleOptions.map((option) => ({
    ...option,
    fare: estimateFare(option.type, distance),
  }));
}

function selectVehicleOption(message: string, options: VehicleFareOption[]) {
  const normalized = message.trim().toLowerCase();
  const choiceNumber = Number(normalized.match(/\d+/)?.[0]);
  if (Number.isInteger(choiceNumber) && choiceNumber >= 1 && choiceNumber <= options.length) {
    return options[choiceNumber - 1];
  }
  return options.find((option) => option.type === normalized || option.label.toLowerCase() === normalized);
}

function latestAssistantAskedForVehicle(messages: ChatMessage[]) {
  const latestAssistant = [...messages].reverse().find((message) => message.role === "assistant");
  return Boolean(latestAssistant?.content.includes("Which ride would you like?"));
}

function isPaymentIntent(message: string) {
  return /\b(pay|payment|pay now|paid)\b/i.test(message);
}

function isVehicleRegistrationIntent(message: string) {
  return /\b(register|add|create|submit)\b.*\b(vehicle|bike|auto|car|sedan|suv)\b|\b(vehicle|bike|auto|car|sedan|suv)\b.*\b(register|add|create|submit)\b/i.test(
    message,
  );
}

function isOutOfBandDuringVehicleChoice(message: string, options: VehicleFareOption[]) {
  const normalized = message.trim().toLowerCase();
  if (!normalized) {
    return false;
  }
  if (selectVehicleOption(normalized, options)) {
    return false;
  }
  if (isBookingIntent(normalized) && hasRoute(normalized)) {
    return false;
  }
  return /\b(status|history|payment|pay|driver|track|where|support|help|cancel|reject|accept|start|complete|profile|settings|admin)\b/i.test(
    normalized,
  );
}

function errorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message === "[object Object]" ? "Please try again." : error.message;
  }
  if (typeof error === "string") {
    return error;
  }
  return "Please try again.";
}

async function resolveGuidedLocation(message: string) {
  if (!/\b(current location|my location)\b/i.test(message)) {
    return message;
  }
  try {
    const location = await currentLocationFromMessage(message);
    return location?.displayName || message;
  } catch {
    return message;
  }
}

function isBookingIntent(message: string) {
  return /\b(book|booking|get|need|want|request|create)\b.*\b(ride|cab|taxi|auto|bike|car)\b|\b(ride|cab|taxi|auto|bike|car)\b.*\b(book|booking|request)\b/i.test(
    message,
  );
}

function parseRouteMessage(message: string) {
  const text = message.trim();
  const labelledMatch = text.match(
    /(?:my\s+)?pickup(?:\s+location)?\s*:\s*(?<pickup>.+?)\s+(?:drop|dropoff|drop-off|destination)(?:\s+location)?\s*:\s*(?<destination>.+)$/i,
  );
  if (labelledMatch?.groups) {
    return cleanRouteParts(labelledMatch.groups.pickup, labelledMatch.groups.destination);
  }

  const fromToMatch = text.match(/\bfrom\s+(?<pickup>.+?)\s+\bto\s+(?<destination>.+)$/i);
  if (fromToMatch?.groups) {
    return cleanRouteParts(fromToMatch.groups.pickup, fromToMatch.groups.destination);
  }

  return { pickup: text, destination: "" };
}

function hasRoute(message: string) {
  return /\bfrom\s+.+?\s+\bto\s+.+/i.test(message) || /\bpickup(?:\s+location)?\s*:.+?(?:drop|dropoff|drop-off|destination)(?:\s+location)?\s*:/i.test(message);
}

function cleanRouteParts(pickup: string, destination: string) {
  return {
    pickup: pickup.replace(/^location\s*:\s*/i, "").replace(/^(?:book|booking|get|need|want|request|create)\s+(?:a\s+)?(?:ride|cab|taxi|auto|bike|car)\s+/i, "").trim(),
    destination: destination.trim(),
  };
}

async function loadAssistantContext(
  message: string,
  messages: ChatMessage[],
  role: string,
): Promise<Record<string, unknown>> {
  const context = role === "customer" ? loadBookingContext() : {};
  const browserLocation = role === "customer" && /\b(current location|my location)\b/i.test(message) ? await currentLocationFromMessage(message) : null;
  const booking = {
    ...((context.booking as Record<string, unknown> | undefined) ?? {}),
    ...(browserLocation ? { pickup: browserLocation } : {}),
  };
  return {
    ...context,
    booking,
    chat_history: messages.slice(-8).map((message) => ({
      role: message.role,
      content: message.content,
    })),
  };
}

async function currentLocationFromMessage(message: string) {
  if (!/\b(current location|my location)\b/i.test(message) || !navigator.geolocation) {
    return null;
  }

  const position = await new Promise<GeolocationPosition>((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 60000,
    });
  });
  return reverseGeocode(
    Number(position.coords.latitude.toFixed(7)),
    Number(position.coords.longitude.toFixed(7)),
  );
}

function loadBookingContext(): Record<string, unknown> {
  try {
    const raw = localStorage.getItem("rydo-booking-context");
    return raw ? ({ booking: JSON.parse(raw) } as Record<string, unknown>) : {};
  } catch {
    return {};
  }
}

function MessageBubble({ role, content, onEdit }: { role: ChatRole; content: string; onEdit?: () => void }) {
  const isUser = role === "user";

  return (
    <div className={`group mb-3 flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-md px-3 py-2 text-sm shadow-sm ${
          isUser ? "bg-black text-white" : "border border-slate-200 bg-white text-slate-800"
        }`}
      >
        <ChatMarkdown content={content} />
      </div>
      {isUser && onEdit && (
        <button
          type="button"
          onClick={onEdit}
          className="ml-2 mt-1 hidden size-7 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-500 hover:text-slate-950 group-hover:flex"
          aria-label="Edit message"
          title="Edit message"
        >
          <Pencil size={14} />
        </button>
      )}
    </div>
  );
}

function IconButton({ label, onClick, children }: { label: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex size-8 items-center justify-center rounded-md text-white/80 hover:bg-white/10 hover:text-white"
      aria-label={label}
      title={label}
    >
      {children}
    </button>
  );
}

function TypingDots() {
  return (
    <span className="flex items-center gap-1">
      <span className="size-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.2s]" />
      <span className="size-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.1s]" />
      <span className="size-1.5 animate-bounce rounded-full bg-slate-400" />
    </span>
  );
}

function loadMessages(storageKey: string): ChatMessage[] {
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw) as ChatMessage[];
    return Array.isArray(parsed) ? parsed.filter((message) => message.role && message.content) : [];
  } catch {
    return [];
  }
}
