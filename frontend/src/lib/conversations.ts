import { apiFetch } from "./api";

export interface Conversation {
    id: string;
    title: string | null;
    created_at: string;
    updated_at: string;
}

export interface ConversationMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    model: string | null;
    created_at: string;
    task_suggestions: TaskSuggestions | null;
    calendar_suggestions: CalendarSuggestions | null;
}

export interface ConversationDetail extends Conversation {
    messages: ConversationMessage[];
}

export interface ExtractedSubtask {
    title: string;
}

export interface ExtractedTask {
    title: string;
    description: string | null;
    priority: "low" | "medium" | "high" | null;
    due_date: string | null;
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
    end_time_inferred: boolean;
}

export interface CalendarSuggestions {
    source_message_id: string | null;
    events: ExtractedCalendarEvent[];
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
    const timezone =
        Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";

    return apiFetch<ConversationMessage[]>(
        `/api/conversations/${conversationId}/messages`,
        {
            method: "POST",
            body: {
                content,
                timezone,
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
