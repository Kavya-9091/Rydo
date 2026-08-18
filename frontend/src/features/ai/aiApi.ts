import { apiClient } from "../../lib/apiClient";

export interface AIConversation {
  id: string;
  user_id: string | null;
  ride_id: string | null;
  conversation_type: string;
  status: string;
  user_message: string;
  assistant_message: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface AIChatResponse {
  reply: string;
  toolExecuted: string | null;
  rideId: string | null;
  conversationId: string;
  metadata: Record<string, unknown> | null;
}

export interface AIProviderStatus {
  provider: string;
  configured: boolean;
  model: string;
}

export async function sendRideAssistantMessage(
  message: string,
  context: Record<string, unknown> = {},
): Promise<AIChatResponse> {
  const response = await apiClient.post<AIChatResponse>("/ai/chat", { message, context });
  return response.data;
}

export async function getAIProviderStatus(): Promise<AIProviderStatus> {
  const response = await apiClient.get<AIProviderStatus>("/ai/provider-status");
  return response.data;
}
