import { apiFetch } from "./api";

export type CalendarEntrySource = "task" | "calendar_event";

export type CalendarEventType =
    | "task_deadline"
    | "meeting"
    | "appointment"
    | "event"
    | "deadline";

export interface CalendarEntry {
    id: string;
    source: CalendarEntrySource;
    title: string;
    description: string | null;
    event_type: CalendarEventType;
    all_day: boolean;
    start_date: string | null;
    end_date: string | null;
    starts_at: string | null;
    ends_at: string | null;
    timezone: string;
    task_id: string | null;
    calendar_event_id: string | null;
    status: "todo" | "in_progress" | "completed" | null;
    priority: "low" | "medium" | "high" | null;
}

export interface CalendarEntriesResponse {
    entries: CalendarEntry[];
}

export interface CalendarEntriesParams {
    start: string;
    end: string;
    timezone: string;
}

export function getCalendarEntries({
    start,
    end,
    timezone,
}: CalendarEntriesParams): Promise<CalendarEntriesResponse> {
    const params = new URLSearchParams({
        start,
        end,
        timezone,
    });

    return apiFetch<CalendarEntriesResponse>(
        `/api/calendar/entries?${params.toString()}`,
    );
}
