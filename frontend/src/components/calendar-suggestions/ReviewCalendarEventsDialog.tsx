import { type SyntheticEvent, useId, useState } from "react";
import { Temporal } from "temporal-polyfill";

import { cn } from "../../lib/cn";
import type { CalendarEventType } from "../../lib/conversations";
import type { ReviewedCalendarEvent } from "../../lib/calendar-suggestions";

import { Button } from "../button";
import { DatePicker } from "../date-picker/DatePicker";
import { Dialog } from "../dialog";
import { Input } from "../input";
import { Select } from "../select/Select";

import { reviewCalendarEventsDialogStyles as styles } from "./ReviewCalendarEventsDialog.styles";
import { TimePicker } from "../time-picker";
import { Checkbox } from "../checkbox/Checkbox";

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

const eventTypeOptions: {
    label: string;
    value: CalendarEventType;
}[] = [
    { label: "Meeting", value: "meeting" },
    { label: "Appointment", value: "appointment" },
    { label: "Event", value: "event" },
    { label: "Deadline", value: "deadline" },
];

function addDays(value: string, days: number): string {
    return Temporal.PlainDate.from(value)
        .add({ days })
        .toString();
}

function zonedDateTimeParts(
    value: string,
    timezone: string,
): {
    date: string;
    time: string;
} {
    const instant = Temporal.Instant.from(value);
    const zoned = instant.toZonedDateTimeISO(timezone);

    return {
        date: zoned.toPlainDate().toString(),
        time: zoned.toPlainTime().toString().slice(0, 5),
    };
}

function toIsoDateTime(
    dateValue: string,
    timeValue: string,
    timezone: string,
): string | null {
    try {
        const date = Temporal.PlainDate.from(dateValue);
        const time = Temporal.PlainTime.from(timeValue);

        const zoned = Temporal.ZonedDateTime.from(
            {
                timeZone: timezone,
                year: date.year,
                month: date.month,
                day: date.day,
                hour: time.hour,
                minute: time.minute,
            },
            {
                disambiguation: "reject",
            },
        );

        return zoned.toInstant().toString();
    } catch {
        // Invalid dates and ambiguous or nonexistent local times
        // require correction before the event can be saved.
        return null;
    }
}

function isValidDate(value: string): boolean {
    try {
        return Temporal.PlainDate.from(value).toString() === value;
    } catch {
        return false;
    }
}

function createDraft(event: CalendarReviewEvent): CalendarDraft {
    const start = event.starts_at
        ? zonedDateTimeParts(
            event.starts_at,
            event.timezone,
        )
        : null;

    const end = event.ends_at
        ? zonedDateTimeParts(
            event.ends_at,
            event.timezone,
        )
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

    const [
        validationError,
        setValidationError,
    ] = useState<string | null>(null);

    const activeEvent = drafts[activeIndex];

    function updateEvent(changes: Partial<CalendarDraft>) {
        setDrafts((previous) =>
            previous.map((event, index) =>
                index === activeIndex
                    ? { ...event, ...changes }
                    : event,
            ),
        );

        setValidationError(null);
    }

    function selectEvent(index: number) {
        setActiveIndex(index);
        setValidationError(null);
    }

    function showValidationError(
        index: number,
        message: string,
    ) {
        setActiveIndex(index);
        setValidationError(message);
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
            ) {
                showValidationError(
                    index,
                    "Please check the event title and description.",
                );
                return;
            }

            if (
                !isValidDate(draft.startDate)
                || !isValidDate(draft.endDate)
            ) {
                showValidationError(
                    index,
                    "Please enter valid start and end dates.",
                );
                return;
            }

            if (draft.all_day) {
                if (draft.endDate < draft.startDate) {
                    showValidationError(
                        index,
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

            const startsAt = toIsoDateTime(
                draft.startDate,
                draft.startTime,
                draft.timezone,
            );

            const endsAt = toIsoDateTime(
                draft.endDate,
                draft.endTime,
                draft.timezone,
            );

            if (!startsAt || !endsAt) {
                showValidationError(
                    index,
                    "The date or time is invalid or falls within a daylight-saving transition. Please choose an unambiguous local time.",
                );
                return;
            }

            const startInstant = Temporal.Instant.from(startsAt);
            const endInstant = Temporal.Instant.from(endsAt);

            if (
                Temporal.Instant.compare(
                    endInstant,
                    startInstant,
                ) <= 0
            ) {
                showValidationError(
                    index,
                    "The end time must be after the start time.",
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
            // Parent handles the notification.
            // Keep the dialog open so the employee can retry.
        });
    }

    if (!activeEvent) {
        return null;
    }

    const footer = (
        <div className={styles.footer}>
            <span className={styles.footerCount}>
                {drafts.length}{" "}
                {drafts.length === 1 ? "event" : "events"} to add
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
            size="xl"
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
                    className={styles.navigation}
                    aria-label="Events to review"
                >
                    {drafts.map((event, index) => (
                        <Button
                            key={event.suggestion_index}
                            type="button"
                            variant="ghost"
                            className={cn(
                                styles.eventTab,
                                index === activeIndex
                                && styles.eventTabActive,
                            )}
                            aria-current={
                                index === activeIndex
                                    ? "step"
                                    : undefined
                            }
                            onClick={() => selectEvent(index)}
                            disabled={saving}
                        >
                            <span className={styles.eventNumber}>
                                {index + 1}
                            </span>

                            <span className={styles.eventTitle}>
                                {event.title.trim() || "Untitled event"}
                            </span>
                        </Button>
                    ))}
                </nav>

                <div className={styles.editor}>
                    <span className={styles.indicator}>
                        Event {activeIndex + 1} of {drafts.length}
                    </span>

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
                                options={eventTypeOptions}
                                value={activeEvent.event_type}
                                onChange={(eventType) => {
                                    if (eventType !== null) {
                                        updateEvent({
                                            event_type: eventType,
                                        });
                                    }
                                }}
                                placeholder="Select event type"
                                disabled={saving}
                            />
                        </div>

                        <div className={styles.field}>
                            <span className={styles.label}>
                                All-day event
                            </span>

                            <div className={styles.checkboxField}>
                                <Checkbox
                                    label="No specific time"
                                    checked={activeEvent.all_day}
                                    onChange={(event) => updateEvent({
                                        all_day: event.target.checked,
                                    })}
                                    disabled={saving}
                                />
                            </div>
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
                                clearable={false}
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
                                clearable={false}
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

                                <TimePicker
                                    id={startTimeId}
                                    value={activeEvent.startTime}
                                    onChange={(time) => updateEvent({
                                        startTime: time ?? "",
                                    })}
                                    disabled={saving}
                                    clearable={false}
                                    interval={15}
                                />
                            </div>

                            <div className={styles.field}>
                                <label
                                    htmlFor={endTimeId}
                                    className={styles.label}
                                >
                                    End time
                                </label>

                                <TimePicker
                                    id={endTimeId}
                                    value={activeEvent.endTime}
                                    onChange={(time) => updateEvent({
                                        endTime: time ?? "",
                                    })}
                                    disabled={saving}
                                    clearable={false}
                                    interval={15}
                                />
                            </div>
                        </div>
                    )}

                    {!activeEvent.all_day
                        && activeEvent.end_time_inferred && (
                        <p className={styles.hint}>
                            NeuroLens assumed the event duration because
                            the original message did not specify an end time.
                            Please review it before saving.
                        </p>
                    )}

                    <p className={styles.hint}>
                        Times are shown in{" "}
                        <strong className="font-medium text-fg">
                            {activeEvent.timezone}
                        </strong>
                    </p>
                </div>
            </form>
        </Dialog>
    );
}
