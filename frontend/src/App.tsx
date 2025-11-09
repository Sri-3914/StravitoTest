import { FormEvent, useMemo, useState } from "react";
import { postChat } from "./api";
import type { ChatMessage, ChatResponse } from "./types";
import { ChatMessage as ChatBubble } from "./components/ChatMessage";

const INITIAL_PROMPT_HINT =
  "Tell me what you need help with or ask a question";

export default function App() {
  const [conversationId, setConversationId] = useState<string>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [form, setForm] = useState({
    message: "",
    market: "",
    category: "",
    timeframe: ""
  });
  const [error, setError] = useState<string>();

  const isSubmitDisabled = useMemo(() => {
    return !form.message.trim() || isLoading;
  }, [form.message, isLoading]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isSubmitDisabled) {
      return;
    }

    const trimmedMessage = form.message.trim();
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      text: trimmedMessage,
      createdAt: new Date()
    };
    setMessages((prev) => [...prev, userMessage]);
    setForm((prev) => ({ ...prev, message: "" }));
    setIsLoading(true);
    setError(undefined);

    try {
      const response = await postChat({
        message: trimmedMessage,
        market: form.market || undefined,
        category: form.category || undefined,
        timeframe: form.timeframe || undefined,
        conversation_id: conversationId
      });
      handleChatResponse(response);
    } catch (err) {
      console.error(err);
      setError(
        "Something went wrong while contacting the assistant. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleChatResponse = (response: ChatResponse) => {
    if (response.conversation_id) {
      setConversationId(response.conversation_id);
    }

    const text = response.follow_up_needed
      ? response.follow_up_prompt ?? "Could you clarify your request?"
      : response.message;

    const role: ChatMessage["role"] = response.follow_up_needed
      ? "system"
      : "assistant";

    const assistantMessage: ChatMessage = {
      id: response.message_id ?? crypto.randomUUID(),
      role,
      text,
      guardrails: response.guardrails,
      sources: response.raw_sources,
      createdAt: new Date()
    };

    setMessages((prev) => [...prev, assistantMessage]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-secondary via-white to-brand-secondary text-brand-dark">
      <div className="flex">
        <aside className="hidden xl:flex xl:w-64 flex-col border-r border-brand-dark/10 bg-white/80 backdrop-blur-sm">
          <div className="px-6 py-6 flex items-center gap-3 border-b border-brand-dark/10">
            <div className="h-10 w-10 rounded-full bg-brand-primary text-white font-semibold flex items-center justify-center">
              iH
            </div>
            <div>
              <p className="font-semibold text-brand-dark">iHub</p>
              <p className="text-xs text-brand-dark/60">Insights workspace</p>
            </div>
          </div>
          <nav className="flex-1 overflow-y-auto px-4 py-6 space-y-6 text-sm">
            <Section title="Home">
              <NavItem label="My Insight Feed" />
              <NavItem label="Library" />
              <NavItem label="Starred" />
              <NavItem label="Assistant" active />
              <NavItem label="My Scrapbooks" />
            </Section>
            <Section title="At Newell Brands">
              <NavItem label="ShopperHub" />
              <NavItem label="TrendsHub" />
              <NavItem label="Brand Health Hub" />
              <NavItem label="Segmentation Hub" />
              <NavItem label="Newsletter Center" />
              <NavItem label="Statista Global Reports" />
              <NavItem label="Quick Start Guide" />
            </Section>
            <Section title="My Collections">
              <NavItem label="Sni Insight Radar" icon="★" />
              <NavItem label="Writing Trends 2025+" icon="★" />
              <NavItem label="Competitor Media Monitoring" icon="★" />
              <NavItem label="US Shopper Census 2025" />
              <NavItem label="Trends One Pager" />
              <NavItem label="Back to School" />
            </Section>
          </nav>
        </aside>

        <main className="flex-1 px-4 sm:px-8 lg:px-16 py-10">
          <header className="max-w-4xl mx-auto mb-8">
            <h1 className="text-3xl font-semibold text-brand-dark mb-2 flex items-center gap-3">
              Assistant
              <span className="inline-flex items-center gap-1 text-xs font-medium bg-brand-primary/10 text-brand-primary px-3 py-1 rounded-full">
                Guardrails enabled
              </span>
            </h1>
            <p className="text-brand-dark/70 max-w-xl">
              Quickly browse a wide range of sources to gather key information
              and uncover new insights. Guardrails ensure evidence transparency,
              market specificity, and safe extrapolations.
            </p>
          </header>

          <section className="max-w-4xl mx-auto glass-panel rounded-3xl p-6 md:p-8 space-y-8">
            <PromptContextForm
              form={form}
              onFormChange={setForm}
              onSubmit={handleSubmit}
              isLoading={isLoading}
              error={error}
            />

            <div className="border-t border-brand-dark/10 pt-6">
              <h2 className="text-sm font-semibold text-brand-dark uppercase tracking-wide mb-4">
                Conversation
              </h2>
              {messages.length === 0 ? (
                <div className="text-brand-dark/60 text-sm">
                  <p className="font-medium mb-2">Start with a guided prompt:</p>
                  <ul className="space-y-2">
                    <li className="rounded-xl border border-dashed border-brand-dark/20 px-4 py-3">
                      Request a category deep dive with clearly defined market
                      and timeframe.
                    </li>
                    <li className="rounded-xl border border-dashed border-brand-dark/20 px-4 py-3">
                      Compare performance across U.S., Mexico, and Brazil and ask
                      for market-specific insights.
                    </li>
                    <li className="rounded-xl border border-dashed border-brand-dark/20 px-4 py-3">
                      Ask for only sources newer than 2022 and flag anything
                      older.
                    </li>
                  </ul>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((message) => (
                    <ChatBubble key={message.id} message={message} />
                  ))}
                  {isLoading && <TypingIndicator />}
                </div>
              )}
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

type PromptContextFormProps = {
  form: {
    message: string;
    market: string;
    category: string;
    timeframe: string;
  };
  onFormChange: (
    updater: (prev: PromptContextFormProps["form"]) => PromptContextFormProps["form"]
  ) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  isLoading: boolean;
  error?: string;
};

function PromptContextForm({
  form,
  onFormChange,
  onSubmit,
  isLoading,
  error
}: PromptContextFormProps) {
  const updateField = (field: keyof typeof form, value: string) => {
    onFormChange((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="flex flex-col gap-3">
        <label className="text-sm font-medium text-brand-dark">Context</label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <TextField
            label="Market"
            placeholder="e.g., United States"
            value={form.market}
            onChange={(value) => updateField("market", value)}
          />
          <TextField
            label="Category"
            placeholder="e.g., Markers"
            value={form.category}
            onChange={(value) => updateField("category", value)}
          />
          <TextField
            label="Timeframe"
            placeholder="e.g., 2023 actuals"
            value={form.timeframe}
            onChange={(value) => updateField("timeframe", value)}
          />
        </div>
      </div>
      <div className="flex flex-col gap-3">
        <label className="text-sm font-medium text-brand-dark" htmlFor="message">
          Ask the assistant
        </label>
        <textarea
          id="message"
          rows={3}
          className="rounded-2xl border border-brand-dark/10 bg-white/80 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-brand-primary/40"
          placeholder={INITIAL_PROMPT_HINT}
          value={form.message}
          onChange={(event) => updateField("message", event.target.value)}
          required
        />
      </div>
      {error && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-2">
          {error}
        </p>
      )}
      <button
        type="submit"
        disabled={!form.message.trim() || isLoading}
        className="inline-flex items-center justify-center gap-2 rounded-full bg-brand-primary text-white px-6 py-3 text-sm font-semibold transition hover:bg-brand-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? "Sending…" : "Send to Assistant"}
      </button>
    </form>
  );
}

type TextFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
};

function TextField({ label, value, onChange, placeholder }: TextFieldProps) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs uppercase tracking-wide text-brand-dark/70 font-semibold">
        {label}
      </span>
      <input
        type="text"
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-2xl border border-brand-dark/10 bg-white/80 px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-primary/40"
      />
    </div>
  );
}

type SectionProps = {
  title: string;
  children: React.ReactNode;
};

function Section({ title, children }: SectionProps) {
  return (
    <div className="space-y-2">
      <p className="text-xs uppercase tracking-wide text-brand-dark/60 font-semibold">
        {title}
      </p>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

type NavItemProps = {
  label: string;
  active?: boolean;
  icon?: string;
};

function NavItem({ label, active, icon }: NavItemProps) {
  return (
    <button
      type="button"
      className={`w-full flex items-center justify-between rounded-xl px-3 py-2 text-left transition ${
        active
          ? "bg-brand-primary text-white"
          : "text-brand-dark/70 hover:bg-brand-primary/10 hover:text-brand-dark"
      }`}
    >
      <span>{label}</span>
      {icon && <span>{icon}</span>}
    </button>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 text-brand-dark/70 text-sm">
      <div className="flex gap-1">
        <span className="w-2 h-2 rounded-full bg-brand-primary animate-bounce" />
        <span className="w-2 h-2 rounded-full bg-brand-primary animate-bounce delay-150" />
        <span className="w-2 h-2 rounded-full bg-brand-primary animate-bounce delay-300" />
      </div>
      Assistant is reviewing sources…
    </div>
  );
}

