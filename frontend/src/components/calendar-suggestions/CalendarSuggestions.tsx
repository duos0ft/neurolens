import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarCheck, CalendarClock, CheckCircle2, Clock3, RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { cn } from "../../lib/cn";
import type {
    CalendarEndTimeSource,
    CalendarSuggestions as CalendarSuggestionsData,
    ExtractedCalendarEvent,
} from "../../lib/conversations";
import {
    getSavedCalendarSuggestions,
    type ReviewedCalendarEvent,
    type SavedCalendarSuggestionsResponse,
    saveReviewedCalendarEvents,
} from "../../lib/calendar-suggestions";
import { Button } from "../button";
import { ReviewCalendarEventsDialog } from "./ReviewCalendarEventsDialog";
import { taskSuggestionsStyles as styles } from "../task-suggestions/TaskSuggestions.styles";

interface CalendarSuggestionsProps {
    messageId: string;
    suggestions: CalendarSuggestionsData;
}

function getEndTimeSource(
    event: ExtractedCalendarEvent,
): CalendarEndTimeSource | null {
    if (event.all_day) {
        return null;
    }

    if (event.end_time_source != null) {
        return event.end_time_source;
    }

    if (event.end_time_inferred === true) {
        return "default";
    }

    if (event.end_time_inferred === false) {
        return "explicit";
    }

    return null;
}

function formatEventSchedule(event: ExtractedCalendarEvent): string {
    if (event.all_day) {
        if (!event.start_date) {
            return "Date not specified";
        }

        const start = new Date(`${event.start_date}T12:00:00Z`);

        return new Intl.DateTimeFormat("en", {
            weekday: "short",
            month: "short",
            day: "numeric",
            year: "numeric",
            timeZone: "UTC",
        }).format(start);
    }

    if (!event.starts_at) {
        return "Time not specified";
    }

    const start = new Date(event.starts_at);

    const formatter = new Intl.DateTimeFormat("en", {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: event.timezone,
    });

    const startLabel = formatter.format(start);

    if (!event.ends_at) {
        return startLabel;
    }

    const end = new Date(event.ends_at);

    const endLabel = new Intl.DateTimeFormat("en", {
        hour: "2-digit",
        minute: "2-digit",
        timeZone: event.timezone,
    }).format(end);

    return `${startLabel} – ${endLabel}`;
}

function getEventTypeLabel(
    eventType: ExtractedCalendarEvent["event_type"],
): string {
    switch (eventType) {
        case "meeting":
            return "Meeting";
        case "appointment":
            return "Appointment";
        case "deadline":
            return "Deadline";
        case "event":
            return "Event";
    }
}

export function CalendarSuggestions({
    messageId,
    suggestions,
}: CalendarSuggestionsProps) {
    const queryClient = useQueryClient();

    const [ selected, setSelected ] = useState<number[]>([]);
    const [ reviewOpen, setReviewOpen ] = useState(false);

    const savedSuggestionsKey = [
        "calendar",
        "saved-suggestions",
        messageId,
    ] as const;

    const savedSuggestionsQuery = useQuery({
        queryKey: savedSuggestionsKey,
        queryFn: () => getSavedCalendarSuggestions(messageId),
        enabled: suggestions.events.length > 0,
    });

    const savedSuggestions = savedSuggestionsQuery.data?.saved ?? [];

    const savedIndices = new Set(
        savedSuggestions.map((suggestion) => suggestion.suggestion_index),
    );

    const savedCount = savedIndices.size;
    const totalCount = suggestions.events.length;

    const selectableIndices = selected.filter(
        (index) => !savedIndices.has(index),
    );

    const selectedEvents = suggestions.events
        .map((event, index) => ({
            ...event,
            suggestion_index: index,
            end_time_source: getEndTimeSource(event),
        }))
        .filter((event) =>
            selectableIndices.includes(event.suggestion_index),
        );

    const saveMutation = useMutation({
        mutationFn: (events: ReviewedCalendarEvent[]) =>
            saveReviewedCalendarEvents(messageId, events),

        onSuccess: (events) => {
            queryClient.setQueryData<SavedCalendarSuggestionsResponse>(
                savedSuggestionsKey,
                (previous) => {
                    const savedByIndex = new Map(
                        (previous?.saved ?? []).map((suggestion) => [
                            suggestion.suggestion_index,
                            suggestion,
                        ]),
                    );

                    for (const event of events) {
                        if (event.source_suggestion_index !== null) {
                            savedByIndex.set(
                                event.source_suggestion_index,
                                {
                                    suggestion_index: event.source_suggestion_index,
                                    event_id: event.id,
                                },
                            );
                        }
                    }

                    return {
                        saved: [ ...savedByIndex.values() ].sort(
                            (a, b) =>
                                a.suggestion_index - b.suggestion_index,
                        ),
                    };
                },
            );

            setReviewOpen(false);
            setSelected([]);

            void queryClient.invalidateQueries({
                queryKey: [ "calendar" ],
            });

            toast.success(
                events.length === 1
                    ? "Event added to Calendar"
                    : `${events.length} events added to Calendar`,
            );
        },

        onError: (error) => {
            toast.error("Unable to save calendar events", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
    });

    function toggleSelected(index: number) {
        if (
            savedIndices.has(index)
            || saveMutation.isPending
            || !savedSuggestionsQuery.isSuccess
        ) {
            return;
        }

        setSelected((previous) =>
            previous.includes(index)
                ? previous.filter((value) => value !== index)
                : [ ...previous, index ],
        );
    }

    if (suggestions.events.length === 0) {
        return null;
    }

    const description = savedCount === totalCount
        ? "All suggested events have been added to your calendar."
        : savedCount > 0
            ? `${savedCount} of ${totalCount} events previously saved. Select any remaining events you'd like to add.`
            : "Select the events you'd like to add. Nothing will be scheduled automatically.";

    return (
        <>
            <section
                className={styles.root}
                aria-label="Suggested calendar events"
            >
                <div className={styles.header}>
                    <h3 className={styles.title}>
                        Suggested calendar events
                    </h3>

                    <span className={styles.count}>
                        {totalCount} found
                    </span>
                </div>

                <p className={styles.description}>
                    {savedSuggestionsQuery.isSuccess
                        ? description
                        : savedSuggestionsQuery.isPending
                            ? "Checking previously saved events..."
                            : "Unable to determine which events have already been saved."}
                </p>

                <div className={styles.list}>
                    {suggestions.events.map((event, index) => {
                        const isSaved = savedIndices.has(index);

                        return (
                            <div
                                key={index}
                                className={cn(
                                    styles.item,
                                    isSaved && styles.itemSaved,
                                )}
                            >
                                {isSaved ? (
                                    <CheckCircle2
                                        className={styles.savedIcon}
                                        aria-label="Saved"
                                    />
                                ) : (
                                    <input
                                        type="checkbox"
                                        checked={selectableIndices.includes(index)}
                                        onChange={() => toggleSelected(index)}
                                        className={styles.checkbox}
                                        disabled={
                                            saveMutation.isPending
                                            || !savedSuggestionsQuery.isSuccess
                                        }
                                        aria-label={`Select ${event.title}`}
                                    />
                                )}

                                <div className={styles.itemContent}>
                                    <div className={styles.itemHeading}>
                                        <span className={styles.itemTitle}>
                                            {event.title}
                                        </span>

                                        {isSaved && (
                                            <span className={styles.savedLabel}>
                                                Added to Calendar
                                            </span>
                                        )}
                                    </div>

                                    {event.description && (
                                        <p className={styles.itemDescription}>
                                            {event.description}
                                        </p>
                                    )}

                                    <div className={styles.metadata}>
                                        <span className="inline-flex items-center gap-1">
                                            <CalendarCheck className="size-3.5"/>
                                            {getEventTypeLabel(event.event_type)}
                                        </span>

                                        <span className="inline-flex items-center gap-1">
                                            <CalendarClock className="size-3.5"/>
                                            {formatEventSchedule(event)}
                                        </span>
                                    </div>

                                    {!event.all_day && (
                                        <div className={styles.metadata}>
                                            <span>
                                                Timezone: {event.timezone}
                                            </span>
                                        </div>
                                    )}

                                    {getEndTimeSource(event) === "default" && (
                                        <p className={styles.itemDescription}>
                                            <span className="inline-flex items-center gap-1.5">
                                                <Clock3 className="size-3.5 shrink-0"/>
                                                End time estimated. Review before saving.
                                            </span>
                                        </p>
                                    )}

                                </div>
                            </div>
                        );
                    })}
                </div>

                <div className={styles.footer}>
                    <span className={styles.selectedCount}>
                        {savedSuggestionsQuery.isPending
                            ? "Checking saved events..."
                            : savedSuggestionsQuery.isError
                                ? "Unable to check saved events"
                                : `${savedCount} previously saved · ${selectableIndices.length} selected`}
                    </span>

                    {savedCount < totalCount && (
                        <Button
                            type="button"
                            variant="primary"
                            disabled={
                                selectableIndices.length === 0
                                || saveMutation.isPending
                                || !savedSuggestionsQuery.isSuccess
                            }
                            onClick={() => setReviewOpen(true)}
                        >
                            <CalendarCheck/>
                            Review & Add to Calendar
                        </Button>
                    )}
                </div>

                {savedSuggestionsQuery.isError && (
                    <Button
                        type="button"
                        variant="ghost"
                        onClick={() => {
                            void savedSuggestionsQuery.refetch();
                        }}
                    >
                        <RefreshCw/>
                        Retry checking saved events
                    </Button>
                )}
            </section>

            {reviewOpen && (
                <ReviewCalendarEventsDialog
                    events={selectedEvents}
                    saving={saveMutation.isPending}
                    onClose={() => {
                        if (!saveMutation.isPending) {
                            setReviewOpen(false);
                        }
                    }}
                    onSave={async (events) => {
                        await saveMutation.mutateAsync(events);
                    }}
                />
            )}
        </>
    );
}
