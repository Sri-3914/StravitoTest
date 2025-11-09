import { clsx } from "clsx";
import type { ChatMessage as ChatMessageType } from "../types";

type Props = {
  message: ChatMessageType;
};

export function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";
  const guardrails = message.guardrails;
  const sources = message.sources ?? guardrails?.source_flags ?? [];

  return (
    <div
      className={clsx("flex gap-3 py-4", {
        "justify-end": isUser
      })}
    >
      {!isUser && (
        <div className="h-10 w-10 flex items-center justify-center rounded-full bg-brand-primary text-white font-semibold">
          iH
        </div>
      )}
      <div
        className={clsx(
          "max-w-3xl rounded-2xl px-5 py-4 shadow-sm text-sm leading-relaxed",
          isUser
            ? "bg-brand-primary/10 text-brand-dark border border-brand-primary/20"
            : "glass-panel text-brand-dark"
        )}
      >
        <p className="whitespace-pre-line">{message.text}</p>
        {!isUser && guardrails && (
          <div className="mt-4 space-y-2 text-xs text-brand-dark/80">
            <GuardrailBadge
              label="Evidence confidence"
              value={guardrails.evidence_confidence}
              description={guardrails.evidence_summary}
            />
            <GuardrailBadge
              label="Market scope"
              value={guardrails.market_scope}
              description={guardrails.tiered_market_focus}
            />
            <GuardrailBadge
              label="Category scope"
              value={guardrails.category_scope}
            />
            <GuardrailBadge
              label="Timeframe scope"
              value={guardrails.timeframe_scope}
            />
          </div>
        )}
        {!isUser && sources.length > 0 && (
          <CitationList sources={sources} />
        )}
      </div>
      {isUser && (
        <div className="h-10 w-10 flex items-center justify-center rounded-full bg-brand-dark text-white font-semibold">
          You
        </div>
      )}
    </div>
  );
}

type GuardrailBadgeProps = {
  label: string;
  value: string;
  description?: string;
};

function GuardrailBadge({ label, value, description }: GuardrailBadgeProps) {
  return (
    <div className="flex flex-col gap-1 border border-brand-dark/10 rounded-xl px-3 py-2 bg-white/70">
      <div className="flex items-center justify-between">
        <span className="uppercase tracking-wide text-[10px] font-semibold text-brand-dark/70">
          {label}
        </span>
        <span className="text-brand-dark font-medium">{value}</span>
      </div>
      {description && (
        <p className="text-[11px] text-brand-dark/70">{description}</p>
      )}
    </div>
  );
}

type CitationListProps = {
  sources: NonNullable<ChatMessageType["sources"]>;
};

function CitationList({ sources }: CitationListProps) {
  return (
    <div className="mt-4 rounded-2xl border border-brand-primary/20 bg-white/85 px-4 py-3 text-xs text-brand-dark">
      <div className="flex items-center gap-2 mb-3">
        <div className="h-6 w-6 flex items-center justify-center rounded-full bg-brand-primary/15 text-brand-primary font-semibold">
          ⓘ
        </div>
        <span className="font-semibold uppercase tracking-wide">Citations</span>
      </div>
      <ol className="space-y-3 list-decimal list-inside">
        {sources.map((source, index) => (
          <li key={`${source.url}-${index}`} className="space-y-1">
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand-primary font-medium hover:underline"
            >
              {source.title}
            </a>
            <div className="text-[11px] text-brand-dark/70 space-x-2">
              <span>{source.label}</span>
              {source.published_at && (
                <span>Published: {new Date(source.published_at).toLocaleDateString()}</span>
              )}
              {source.is_outdated && (
                <span className="text-red-600 font-medium">
                  Flagged: older than 3 years
                </span>
              )}
            </div>
            {source.description && (
              <p className="text-[11px] text-brand-dark/80">{source.description}</p>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}

