import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMemo, useState } from "react";
import { postChat } from "./api";
import { ChatMessage as ChatBubble } from "./components/ChatMessage";
const INITIAL_PROMPT_HINT = "Tell me what you need help with or ask a question";
export default function App() {
    const [conversationId, setConversationId] = useState();
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [form, setForm] = useState({
        message: "",
        market: "",
        category: "",
        timeframe: ""
    });
    const [error, setError] = useState();
    const isSubmitDisabled = useMemo(() => {
        return !form.message.trim() || isLoading;
    }, [form.message, isLoading]);
    const handleSubmit = async (event) => {
        event.preventDefault();
        if (isSubmitDisabled) {
            return;
        }
        const trimmedMessage = form.message.trim();
        const userMessage = {
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
        }
        catch (err) {
            console.error(err);
            setError("Something went wrong while contacting the assistant. Please try again.");
        }
        finally {
            setIsLoading(false);
        }
    };
    const handleChatResponse = (response) => {
        if (response.conversation_id) {
            setConversationId(response.conversation_id);
        }
        const text = response.follow_up_needed
            ? response.follow_up_prompt ?? "Could you clarify your request?"
            : response.message;
        const role = response.follow_up_needed
            ? "system"
            : "assistant";
        const assistantMessage = {
            id: response.message_id ?? crypto.randomUUID(),
            role,
            text,
            guardrails: response.guardrails,
            sources: response.raw_sources,
            createdAt: new Date()
        };
        setMessages((prev) => [...prev, assistantMessage]);
    };
    return (_jsx("div", { className: "min-h-screen bg-gradient-to-br from-brand-secondary via-white to-brand-secondary text-brand-dark", children: _jsxs("div", { className: "flex", children: [_jsxs("aside", { className: "hidden xl:flex xl:w-64 flex-col border-r border-brand-dark/10 bg-white/80 backdrop-blur-sm", children: [_jsxs("div", { className: "px-6 py-6 flex items-center gap-3 border-b border-brand-dark/10", children: [_jsx("div", { className: "h-10 w-10 rounded-full bg-brand-primary text-white font-semibold flex items-center justify-center", children: "iH" }), _jsxs("div", { children: [_jsx("p", { className: "font-semibold text-brand-dark", children: "iHub" }), _jsx("p", { className: "text-xs text-brand-dark/60", children: "Insights workspace" })] })] }), _jsxs("nav", { className: "flex-1 overflow-y-auto px-4 py-6 space-y-6 text-sm", children: [_jsxs(Section, { title: "Home", children: [_jsx(NavItem, { label: "My Insight Feed" }), _jsx(NavItem, { label: "Library" }), _jsx(NavItem, { label: "Starred" }), _jsx(NavItem, { label: "Assistant", active: true }), _jsx(NavItem, { label: "My Scrapbooks" })] }), _jsxs(Section, { title: "At Newell Brands", children: [_jsx(NavItem, { label: "ShopperHub" }), _jsx(NavItem, { label: "TrendsHub" }), _jsx(NavItem, { label: "Brand Health Hub" }), _jsx(NavItem, { label: "Segmentation Hub" }), _jsx(NavItem, { label: "Newsletter Center" }), _jsx(NavItem, { label: "Statista Global Reports" }), _jsx(NavItem, { label: "Quick Start Guide" })] }), _jsxs(Section, { title: "My Collections", children: [_jsx(NavItem, { label: "Sni Insight Radar", icon: "\u2605" }), _jsx(NavItem, { label: "Writing Trends 2025+", icon: "\u2605" }), _jsx(NavItem, { label: "Competitor Media Monitoring", icon: "\u2605" }), _jsx(NavItem, { label: "US Shopper Census 2025" }), _jsx(NavItem, { label: "Trends One Pager" }), _jsx(NavItem, { label: "Back to School" })] })] })] }), _jsxs("main", { className: "flex-1 px-4 sm:px-8 lg:px-16 py-10", children: [_jsxs("header", { className: "max-w-4xl mx-auto mb-8", children: [_jsxs("h1", { className: "text-3xl font-semibold text-brand-dark mb-2 flex items-center gap-3", children: ["Assistant", _jsx("span", { className: "inline-flex items-center gap-1 text-xs font-medium bg-brand-primary/10 text-brand-primary px-3 py-1 rounded-full", children: "Guardrails enabled" })] }), _jsx("p", { className: "text-brand-dark/70 max-w-xl", children: "Quickly browse a wide range of sources to gather key information and uncover new insights. Guardrails ensure evidence transparency, market specificity, and safe extrapolations." })] }), _jsxs("section", { className: "max-w-4xl mx-auto glass-panel rounded-3xl p-6 md:p-8 space-y-8", children: [_jsx(PromptContextForm, { form: form, onFormChange: setForm, onSubmit: handleSubmit, isLoading: isLoading, error: error }), _jsxs("div", { className: "border-t border-brand-dark/10 pt-6", children: [_jsx("h2", { className: "text-sm font-semibold text-brand-dark uppercase tracking-wide mb-4", children: "Conversation" }), messages.length === 0 ? (_jsxs("div", { className: "text-brand-dark/60 text-sm", children: [_jsx("p", { className: "font-medium mb-2", children: "Start with a guided prompt:" }), _jsxs("ul", { className: "space-y-2", children: [_jsx("li", { className: "rounded-xl border border-dashed border-brand-dark/20 px-4 py-3", children: "Request a category deep dive with clearly defined market and timeframe." }), _jsx("li", { className: "rounded-xl border border-dashed border-brand-dark/20 px-4 py-3", children: "Compare performance across U.S., Mexico, and Brazil and ask for market-specific insights." }), _jsx("li", { className: "rounded-xl border border-dashed border-brand-dark/20 px-4 py-3", children: "Ask for only sources newer than 2022 and flag anything older." })] })] })) : (_jsxs("div", { className: "space-y-4", children: [messages.map((message) => (_jsx(ChatBubble, { message: message }, message.id))), isLoading && _jsx(TypingIndicator, {})] }))] })] })] })] }) }));
}
function PromptContextForm({ form, onFormChange, onSubmit, isLoading, error }) {
    const updateField = (field, value) => {
        onFormChange((prev) => ({ ...prev, [field]: value }));
    };
    return (_jsxs("form", { onSubmit: onSubmit, className: "space-y-4", children: [_jsxs("div", { className: "flex flex-col gap-3", children: [_jsx("label", { className: "text-sm font-medium text-brand-dark", children: "Context" }), _jsxs("div", { className: "grid grid-cols-1 md:grid-cols-3 gap-3", children: [_jsx(TextField, { label: "Market", placeholder: "e.g., United States", value: form.market, onChange: (value) => updateField("market", value) }), _jsx(TextField, { label: "Category", placeholder: "e.g., Markers", value: form.category, onChange: (value) => updateField("category", value) }), _jsx(TextField, { label: "Timeframe", placeholder: "e.g., 2023 actuals", value: form.timeframe, onChange: (value) => updateField("timeframe", value) })] })] }), _jsxs("div", { className: "flex flex-col gap-3", children: [_jsx("label", { className: "text-sm font-medium text-brand-dark", htmlFor: "message", children: "Ask the assistant" }), _jsx("textarea", { id: "message", rows: 3, className: "rounded-2xl border border-brand-dark/10 bg-white/80 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-brand-primary/40", placeholder: INITIAL_PROMPT_HINT, value: form.message, onChange: (event) => updateField("message", event.target.value), required: true })] }), error && (_jsx("p", { className: "text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-2", children: error })), _jsx("button", { type: "submit", disabled: !form.message.trim() || isLoading, className: "inline-flex items-center justify-center gap-2 rounded-full bg-brand-primary text-white px-6 py-3 text-sm font-semibold transition hover:bg-brand-primary/90 disabled:opacity-50 disabled:cursor-not-allowed", children: isLoading ? "Sending…" : "Send to Assistant" })] }));
}
function TextField({ label, value, onChange, placeholder }) {
    return (_jsxs("div", { className: "flex flex-col gap-1", children: [_jsx("span", { className: "text-xs uppercase tracking-wide text-brand-dark/70 font-semibold", children: label }), _jsx("input", { type: "text", value: value, placeholder: placeholder, onChange: (event) => onChange(event.target.value), className: "rounded-2xl border border-brand-dark/10 bg-white/80 px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-primary/40" })] }));
}
function Section({ title, children }) {
    return (_jsxs("div", { className: "space-y-2", children: [_jsx("p", { className: "text-xs uppercase tracking-wide text-brand-dark/60 font-semibold", children: title }), _jsx("div", { className: "space-y-1", children: children })] }));
}
function NavItem({ label, active, icon }) {
    return (_jsxs("button", { type: "button", className: `w-full flex items-center justify-between rounded-xl px-3 py-2 text-left transition ${active
            ? "bg-brand-primary text-white"
            : "text-brand-dark/70 hover:bg-brand-primary/10 hover:text-brand-dark"}`, children: [_jsx("span", { children: label }), icon && _jsx("span", { children: icon })] }));
}
function TypingIndicator() {
    return (_jsxs("div", { className: "flex items-center gap-2 text-brand-dark/70 text-sm", children: [_jsxs("div", { className: "flex gap-1", children: [_jsx("span", { className: "w-2 h-2 rounded-full bg-brand-primary animate-bounce" }), _jsx("span", { className: "w-2 h-2 rounded-full bg-brand-primary animate-bounce delay-150" }), _jsx("span", { className: "w-2 h-2 rounded-full bg-brand-primary animate-bounce delay-300" })] }), "Assistant is reviewing sources\u2026"] }));
}
