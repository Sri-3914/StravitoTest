import axios from "axios";
import type { ChatRequest, ChatResponse } from "./types";

const client = axios.create({
  baseURL: "/api",
  timeout: 30000
});

export async function postChat(request: ChatRequest): Promise<ChatResponse> {
  const { data } = await client.post<ChatResponse>("/chat", request);
  return data;
}

