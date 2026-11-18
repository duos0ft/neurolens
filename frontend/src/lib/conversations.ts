import { apiFetch } from "./api";

export interface Conversation {
    id: string;
    title: string | null;
    created_at: string;
    updated_at: string;
}

export interface ConversationClarifications {
    version: 1;
    questions: string[];
}

export interface ConversationCapabilityMetadata {
    capabilities: string[];
    sources?: unknown[];
}

export interface ConversationMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    model: string | null;
    created_at: string;
    task_suggestions: TaskSuggestions | null;
    calendar_suggestions: CalendarSuggestions | null;
    clarifications: ConversationClarifications | null;
    policy_citations: PolicyCitation[] | null;
    sentiment_analysis: SentimentAnalysisResponse | null;
    capability_metadata: ConversationCapabilityMetadata | null;
}

export interface ConversationDetail extends Conversation {
    messages: ConversationMessage[];
}

export interface ExtractedSubtask {
    title: string;
}

export interface ConversationFeatures {
    enable_sentiment_analysis: boolean;
}

export interface ExtractedTask {
    title: string;
    description: string | null;
    priority: "low" | "medium" | "high" | null;
    due_date: string | null;
    due_time: string | null;
    source_text: string | null;
    subtasks: ExtractedSubtask[];
}

export interface TaskSuggestions {
    source_message_id: string | null;
    tasks: ExtractedTask[];
}

export type CalendarEventType =
    | "meeting"
    | "appointment"
    | "event"
    | "deadline";

export type CalendarEndTimeSource =
    | "explicit"
    | "duration"
    | "default";

export interface ExtractedCalendarEvent {
    title: string;
    description: string | null;
    event_type: CalendarEventType;
    all_day: boolean;
    start_date: string | null;
    end_date: string | null;
    starts_at: string | null;
    ends_at: string | null;
    timezone: string;
    source_text: string | null;
    end_time_source?: CalendarEndTimeSource | null;
    end_time_inferred?: boolean;
}

export interface CalendarSuggestions {
    source_message_id: string | null;
    events: ExtractedCalendarEvent[];
}

export interface PolicyCitation {
    reference: string;
    document_id: string;
    version_id: string;
    document_title: string;
    version_number: number;
    page_number: number | null;
    chunk_id: string;
}

export type SentimentLabel =
    | "negative"
    | "neutral"
    | "positive";

export interface SentimentAnalysisResponse {
    label: SentimentLabel;
    confidence: number;
    model: string;
    analyzed_at: string;
}

export function getConversations(): Promise<Conversation[]> {
    return apiFetch<Conversation[]>("/api/conversations");
}

export function getConversation(
    conversationId: string,
): Promise<ConversationDetail> {
    return apiFetch<ConversationDetail>(
        `/api/conversations/${conversationId}`,
    );
}

export function createConversation(
    title?: string,
): Promise<Conversation> {
    return apiFetch<Conversation>("/api/conversations", {
        method: "POST",
        body: {
            title: title ?? null,
        },
    });
}

export function sendConversationMessage(
    conversationId: string,
    content: string,
): Promise<ConversationMessage[]> {
    return apiFetch<ConversationMessage[]>(
        `/api/conversations/${conversationId}/messages`,
        {
            method: "POST",
            body: {
                content,
            },
        },
    );
}

export function deleteConversation(
    conversationId: string,
): Promise<void> {
    return apiFetch<void>(
        `/api/conversations/${conversationId}`,
        {
            method: "DELETE",
        },
    );
}

export function renameConversation(
    conversationId: string,
    title: string,
): Promise<Conversation> {
    return apiFetch<Conversation>(
        `/api/conversations/${conversationId}`,
        {
            method: "PATCH",
            body: {
                title,
            },
        },
    );
}

export function analyzeMessageSentiment(
    conversationId: string,
    messageId: string,
): Promise<SentimentAnalysisResponse> {
    return apiFetch<SentimentAnalysisResponse>(
        `/api/conversations/${encodeURIComponent(conversationId)}/messages/${encodeURIComponent(messageId)}/analyze-sentiment`,
        {
            method: "POST",
        },
    );
}

export function getConversationFeatures(): Promise<ConversationFeatures> {
    return apiFetch<ConversationFeatures>(
        "/api/conversations/features",
    );
}
