export type GuardrailSourceFlag = {
  title: string;
  url: string;
  type: string;
  description: string;
  published_at?: string;
  is_outdated?: boolean;
  age_in_years?: number;
  label: string;
};

export type GuardrailAssessment = {
  evidence_confidence: string;
  evidence_summary: string;
  market_scope: string;
  category_scope: string;
  timeframe_scope: string;
  tiered_market_focus: string;
  fabrication_warning?: string | null;
  source_flags: GuardrailSourceFlag[];
};

export type ChatResponse = {
  conversation_id?: string;
  message_id?: string;
  message: string;
  guardrails?: GuardrailAssessment;
  raw_sources: GuardrailSourceFlag[];
  follow_up_needed: boolean;
  follow_up_prompt?: string | null;
};

export type ChatRequest = {
  message: string;
  market?: string;
  category?: string;
  timeframe?: string;
  conversation_id?: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  text: string;
  guardrails?: GuardrailAssessment;
  sources?: GuardrailSourceFlag[];
  createdAt: Date;
};

