import { apiFetch } from "./api";
import type { CalendarEventType } from "./conversations";

export interface ReviewedCalendarEvent {
    suggestion_index: number;
    title: string;
    description: string | null;
    event_type: CalendarEventType;
    all_day: boolean;
    start_date: string | null;
    end_date: string | null;
    starts_at: string | null;
    ends_at: string | null;
    timezone: string;
}

export interface SavedCalendarSuggestion {
    suggestion_index: number;
    event_id: string;
}

export interface SavedCalendarSuggestionsResponse {
    saved: SavedCalendarSuggestion[];
}

export interface SavedCalendarEvent {
    id: string;
    title: string;
    description: string | null;
    event_type: CalendarEventType;
    all_day: boolean;
    start_date: string | null;
    end_date: string | null;
    starts_at: string | null;
    ends_at: string | null;
    timezone: string;
    source_message_id: string | null;
    source_suggestion_index: number | null;
    created_at: string;
    updated_at: string;
}

export function getSavedCalendarSuggestions(
    messageId: string,
): Promise<SavedCalendarSuggestionsResponse> {
    return apiFetch<SavedCalendarSuggestionsResponse>(
        `/api/calendar/suggestions/${messageId}/saved`,
    );
}

export function saveReviewedCalendarEvents(
    messageId: string,
    events: ReviewedCalendarEvent[],
): Promise<SavedCalendarEvent[]> {
    return apiFetch<SavedCalendarEvent[]>(
        `/api/calendar/suggestions/${messageId}/save`,
        {
            method: "POST",
            body: {
                events,
            },
        },
    );
}
