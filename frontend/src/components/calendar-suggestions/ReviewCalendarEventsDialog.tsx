import { type SyntheticEvent, useId, useState } from "react";

import type { CalendarEventType } from "../../lib/conversations";
import type { ReviewedCalendarEvent } from "../../lib/calendar-suggestions";
import { Button } from "../button";
import { DatePicker } from "../date-picker/DatePicker";
import { Dialog } from "../dialog";
import { Input } from "../input";
import { Select } from "../select/Select";
import { reviewTasksDialogStyles as styles } from "../task-suggestions/ReviewTasksDialog.styles";

interface CalendarReviewEvent extends ReviewedCalendarEvent {
    end_time_inferred?: boolean;
}

interface ReviewCalendarEventsDialogProps {
    events: CalendarReviewEvent[];
    saving: boolean;
    onClose: () => void;
    onSave: (events: ReviewedCalendarEvent[]) => Promise<void>;
}

interface CalendarDraft {
    suggestion_index: number;
    title: string;
    description: string | null;
    event_type: CalendarEventType;
    all_day: boolean;
    startDate: string;
    endDate: string;
    startTime: string;
    endTime: string;
    timezone: string;
    end_time_inferred: boolean;
}

function addDays(value: string, days: number): string {
    const date = new Date(`${value}T12:00:00Z`);
    date.setUTCDate(date.getUTCDate() + days);
    return date.toISOString().slice(0, 10);
}

function localDateTime(value: string): {
    date: string;
    time: string;
} {
    const date = new Date(value);

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hour = String(date.getHours()).padStart(2, "0");
    const minute = String(date.getMinutes()).padStart(2, "0");

    return {
        date: `${year}-${month}-${day}`,
        time: `${hour}:${minute}`,
    };
}

function toIsoDateTime(
    dateValue: string,
    timeValue: string,
): string | null {
    if (
        !/^\d{4}-\d{2}-\d{2}$/.test(dateValue)
        || !/^\d{2}:\d{2}$/.test(timeValue)
    ) {
        return null;
    }

    const [ year, month, day ] = dateValue.split("-").map(Number);
    const [ hour, minute ] = timeValue.split(":").map(Number);

    const date = new Date(
        year,
        month - 1,
        day,
        hour,
        minute,
    );

    if (
        date.getFullYear() !== year
        || date.getMonth() !== month - 1
        || date.getDate() !== day
        || date.getHours() !== hour
        || date.getMinutes() !== minute
    ) {
        return null;
    }

    return date.toISOString();
}

function createDraft(event: CalendarReviewEvent): CalendarDraft {
    const start = event.starts_at
        ? localDateTime(event.starts_at)
        : null;

    const end = event.ends_at
        ? localDateTime(event.ends_at)
        : null;

    return {
        suggestion_index: event.suggestion_index,
        title: event.title,
        description: event.description,
        event_type: event.event_type,
        all_day: event.all_day,
        startDate: event.all_day
            ? event.start_date ?? ""
            : start?.date ?? "",
        endDate: event.all_day
            ? event.end_date
                ? addDays(event.end_date, -1)
                : ""
            : end?.date ?? "",
        startTime: start?.time ?? "09:00",
        endTime: end?.time ?? "10:00",
        timezone: event.timezone,
        end_time_inferred: event.end_time_inferred ?? false,
    };
}

export function ReviewCalendarEventsDialog({
    events,
    saving,
    onClose,
    onSave,
}: ReviewCalendarEventsDialogProps) {
    const formId = useId();
    const titleId = useId();
    const descriptionId = useId();
    const startDateId = useId();
    const endDateId = useId();
    const startTimeId = useId();
    const endTimeId = useId();

    const [ drafts, setDrafts ] = useState<CalendarDraft[]>(
        () => events.map(createDraft),
    );

    const [ activeIndex, setActiveIndex ] = useState(0);
    const [ validationError, setValidationError ] = useState<string | null>(null);

    const activeEvent = drafts[activeIndex];

    const browserTimezone =
        Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";

    function updateEvent(changes: Partial<CalendarDraft>) {
        setDrafts((previous) => previous.map((event, index) =>
            index === activeIndex
                ? { ...event, ...changes }
                : event,
        ));

        setValidationError(null);
    }

    function selectEvent(index: number) {
        setActiveIndex(index);
        setValidationError(null);
    }

    function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
        event.preventDefault();

        if (saving) {
            return;
        }

        const reviewedEvents: ReviewedCalendarEvent[] = [];

        for (const [ index, draft ] of drafts.entries()) {
            const title = draft.title.trim().replace(/\s+/g, " ");
            const description = draft.description?.trim() || null;

            if (
                !title
                || title.length > 200
                || (description?.length ?? 0) > 2000
                || !draft.startDate
                || !draft.endDate
            ) {
                setActiveIndex(index);
                setValidationError(
                    "Please check the event title, description and dates.",
                );
                return;
            }

            if (draft.all_day) {
                if (draft.endDate < draft.startDate) {
                    setActiveIndex(index);
                    setValidationError(
                        "The end date cannot be before the start date.",
                    );
                    return;
                }

                reviewedEvents.push({
                    suggestion_index: draft.suggestion_index,
                    title,
                    description,
                    event_type: draft.event_type,
                    all_day: true,
                    start_date: draft.startDate,
                    end_date: addDays(draft.endDate, 1),
                    starts_at: null,
                    ends_at: null,
                    timezone: draft.timezone,
                });

                continue;
            }

            if (draft.timezone !== browserTimezone) {
                setActiveIndex(index);
                setValidationError(
                    `This event uses ${draft.timezone}, but your browser uses ${browserTimezone}. Time editing in another timezone is not supported yet.`,
                );
                return;
            }

            const startsAt = toIsoDateTime(
                draft.startDate,
                draft.startTime,
            );

            const endsAt = toIsoDateTime(
                draft.endDate,
                draft.endTime,
            );

            if (
                !startsAt
                || !endsAt
                || new Date(endsAt).getTime() <= new Date(startsAt).getTime()
            ) {
                setActiveIndex(index);
                setValidationError(
                    "Please enter valid start and end times. The end must be after the start.",
                );
                return;
            }

            reviewedEvents.push({
                suggestion_index: draft.suggestion_index,
                title,
                description,
                event_type: draft.event_type,
                all_day: false,
                start_date: null,
                end_date: null,
                starts_at: startsAt,
                ends_at: endsAt,
                timezone: draft.timezone,
            });
        }

        setValidationError(null);

        void onSave(reviewedEvents).catch(() => {
            // The parent handles the notification.
            // Keep the dialog open so the user can retry.
        });
    }

    if (!activeEvent) {
        return null;
    }

    const footer = (
        <div className={styles.footer}>
            <span className={styles.footerCount}>
                {drafts.length} {drafts.length === 1 ? "event" : "events"} to add
            </span>

            <div className={styles.footerActions}>
                <Button
                    type="button"
                    variant="secondary"
                    disabled={saving}
                    onClick={onClose}
                >
                    Cancel
                </Button>

                <Button
                    type="submit"
                    form={formId}
                    variant="primary"
                    disabled={saving}
                >
                    {saving ? "Saving..." : "Add to Calendar"}
                </Button>
            </div>
        </div>
    );

    return (
        <Dialog
            open
            onClose={onClose}
            title="Review calendar events"
            description="Review the details before adding events to your calendar."
            size="lg"
            closeDisabled={saving}
            footer={footer}
        >
            <form
                id={formId}
                className={styles.form}
                onSubmit={handleSubmit}
                noValidate
            >
                <nav
                    className={styles.taskNavigation}
                    aria-label="Events to review"
                >
                    {drafts.map((event, index) => (
                        <Button
                            key={event.suggestion_index}
                            type="button"
                            variant="ghost"
                            className={
                                index === activeIndex
                                    ? styles.taskTabActive
                                    : styles.taskTab
                            }
                            aria-current={
                                index === activeIndex ? "step" : undefined
                            }
                            onClick={() => selectEvent(index)}
                            disabled={saving}
                        >
                            <span className={styles.taskNumber}>
                                {index + 1}
                            </span>

                            <span className={styles.taskTabTitle}>
                                {event.title.trim() || "Untitled event"}
                            </span>
                        </Button>
                    ))}
                </nav>

                <div className={styles.editor}>
                    <div className={styles.editorHeader}>
                        <span className={styles.taskIndicator}>
                            Event {activeIndex + 1} of {drafts.length}
                        </span>
                    </div>

                    {validationError && (
                        <p
                            className={styles.validationError}
                            role="alert"
                        >
                            {validationError}
                        </p>
                    )}

                    <div className={styles.field}>
                        <label
                            htmlFor={titleId}
                            className={styles.label}
                        >
                            Event title
                        </label>

                        <Input
                            id={titleId}
                            inputSize="md"
                            value={activeEvent.title}
                            onChange={(event) => updateEvent({
                                title: event.target.value,
                            })}
                            maxLength={200}
                            disabled={saving}
                            aria-required="true"
                        />
                    </div>

                    <div className={styles.field}>
                        <label
                            htmlFor={descriptionId}
                            className={styles.label}
                        >
                            Description
                        </label>

                        <textarea
                            id={descriptionId}
                            className={styles.textarea}
                            value={activeEvent.description ?? ""}
                            onChange={(event) => updateEvent({
                                description: event.target.value,
                            })}
                            maxLength={2000}
                            rows={3}
                            disabled={saving}
                            placeholder="Add event details..."
                        />
                    </div>

                    <div className={styles.fieldGrid}>
                        <div className={styles.field}>
                            <label className={styles.label}>
                                Event type
                            </label>

                            <Select<CalendarEventType>
                                options={[
                                    { label: "Meeting", value: "meeting" },
                                    { label: "Appointment", value: "appointment" },
                                    { label: "Event", value: "event" },
                                    { label: "Deadline", value: "deadline" },
                                ]}
                                value={activeEvent.event_type}
                                onChange={(event_type) => {
                                    if (event_type) {
                                        updateEvent({ event_type });
                                    }
                                }}
                                disabled={saving}
                            />
                        </div>

                        <div className={styles.field}>
                            <label className={styles.label}>
                                All-day event
                            </label>

                            <label className="flex min-h-10 items-center gap-2 text-sm text-fg">
                                <input
                                    type="checkbox"
                                    checked={activeEvent.all_day}
                                    onChange={(event) => updateEvent({
                                        all_day: event.target.checked,
                                    })}
                                    disabled={saving}
                                    className="size-4 accent-primary"
                                />
                                No specific time
                            </label>
                        </div>
                    </div>

                    <div className={styles.fieldGrid}>
                        <div className={styles.field}>
                            <label
                                htmlFor={startDateId}
                                className={styles.label}
                            >
                                Start date
                            </label>

                            <DatePicker
                                id={startDateId}
                                value={activeEvent.startDate || null}
                                onChange={(date) => updateEvent({
                                    startDate: date ?? "",
                                })}
                                disabled={saving}
                            />
                        </div>

                        <div className={styles.field}>
                            <label
                                htmlFor={endDateId}
                                className={styles.label}
                            >
                                End date
                            </label>

                            <DatePicker
                                id={endDateId}
                                value={activeEvent.endDate || null}
                                onChange={(date) => updateEvent({
                                    endDate: date ?? "",
                                })}
                                disabled={saving}
                            />
                        </div>
                    </div>

                    {!activeEvent.all_day && (
                        <div className={styles.fieldGrid}>
                            <div className={styles.field}>
                                <label
                                    htmlFor={startTimeId}
                                    className={styles.label}
                                >
                                    Start time
                                </label>

                                <input
                                    id={startTimeId}
                                    type="time"
                                    className={styles.select}
                                    value={activeEvent.startTime}
                                    onChange={(event) => updateEvent({
                                        startTime: event.target.value,
                                    })}
                                    disabled={saving}
                                />
                            </div>

                            <div className={styles.field}>
                                <label
                                    htmlFor={endTimeId}
                                    className={styles.label}
                                >
                                    End time
                                </label>

                                <input
                                    id={endTimeId}
                                    type="time"
                                    className={styles.select}
                                    value={activeEvent.endTime}
                                    onChange={(event) => updateEvent({
                                        endTime: event.target.value,
                                    })}
                                    disabled={saving}
                                />
                            </div>
                        </div>
                    )}

                    {!activeEvent.all_day && activeEvent.end_time_inferred && (
                        <p className="text-xs leading-5 text-fg-muted">
                            NeuroLens assumed the meeting duration because
                            the original message did not specify an end time.
                            Please review it before saving.
                        </p>
                    )}

                    <p className="text-xs text-fg-muted">
                        Timezone: {activeEvent.timezone}
                    </p>
                </div>
            </form>
        </Dialog>
    );
}
