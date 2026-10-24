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
}

export interface ConversationDetail extends Conversation {
    messages: ConversationMessage[];
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
            body: { title },
        },
    );
}
