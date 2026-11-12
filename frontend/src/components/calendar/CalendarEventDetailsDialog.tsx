import { CalendarCheck, CalendarDays, CheckCircle2, Clock3, Flag, Globe2, Users } from "lucide-react";
import { Temporal } from "temporal-polyfill";

import { Button } from "../button";
import { Dialog } from "../dialog";
import type { CalendarEntry } from "../../lib/calendar";
import { cn } from "../../lib/cn";
import { calendarEventDetailsDialogStyles as styles } from "./CalendarEventDetailsDialog.styles";

interface CalendarEventDetailsDialogProps {
    entry: CalendarEntry | null;
    timezone: string;
    onClose: () => void;
    onViewTask?: (taskId: string) => void;
}

const eventTypeLabels: Record<CalendarEntry["event_type"], string> = {
    task_deadline: "Task deadline",
    meeting: "Meeting",
    appointment: "Appointment",
    event: "Event",
    deadline: "Deadline",
};

function getEventIcon(type: CalendarEntry["event_type"]) {
    switch (type) {
        case "task_deadline":
            return CheckCircle2;
        case "meeting":
            return Users;
        case "appointment":
            return CalendarCheck;
        case "deadline":
            return Flag;
        default:
            return CalendarDays;
    }
}

function formatDate(value: string): string {
    const date = Temporal.PlainDate.from(value);

    return new Intl.DateTimeFormat("en", {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric",
        timeZone: "UTC",
    }).format(
        new Date(`${date.toString()}T12:00:00Z`),
    );
}

function formatDateTime(
    value: string,
    timezone: string,
): {
    date: string;
    time: string;
    day: string;
} {
    const date = Temporal.Instant
        .from(value)
        .toZonedDateTimeISO(timezone);

    return {
        date: formatDate(date.toPlainDate().toString()),
        time: [
            String(date.hour).padStart(2, "0"),
            String(date.minute).padStart(2, "0"),
        ].join(":"),
        day: date.toPlainDate().toString(),
    };
}

function getEventDateDetails(
    entry: CalendarEntry,
    timezone: string,
): {
    dateLabel: string;
    timeLabel: string | null;
} {
    if (entry.all_day) {
        if (!entry.start_date) {
            return {
                dateLabel: "Date unavailable",
                timeLabel: null,
            };
        }

        const start = Temporal.PlainDate.from(entry.start_date);

        if (!entry.end_date) {
            return {
                dateLabel: formatDate(start.toString()),
                timeLabel: "All day",
            };
        }

        const lastDay = Temporal.PlainDate
            .from(entry.end_date)
            .subtract({ days: 1 });

        const isSingleDay = Temporal.PlainDate.compare(
            start,
            lastDay,
        ) >= 0;

        return {
            dateLabel: isSingleDay
                ? formatDate(start.toString())
                : `${formatDate(start.toString())} – ${formatDate(lastDay.toString())}`,
            timeLabel: "All day",
        };
    }

    if (!entry.starts_at) {
        return {
            dateLabel: "Date unavailable",
            timeLabel: null,
        };
    }

    const start = formatDateTime(entry.starts_at, timezone);

    if (!entry.ends_at) {
        return {
            dateLabel: start.date,
            timeLabel: start.time,
        };
    }

    const end = formatDateTime(entry.ends_at, timezone);

    const isTaskDeadline = entry.event_type === "task_deadline";

    return {
        dateLabel: start.day === end.day
            ? start.date
            : `${start.date} – ${end.date}`,
        timeLabel: isTaskDeadline
            ? start.time
            : `${start.time} – ${end.time}`,
    };
}

export function CalendarEventDetailsDialog({
    entry,
    timezone,
    onClose,
    onViewTask,
}: CalendarEventDetailsDialogProps) {
    if (!entry) {
        return null;
    }

    const Icon = getEventIcon(entry.event_type);

    const completed = entry.event_type === "task_deadline"
        && entry.status === "completed";

    const dateDetails = getEventDateDetails(entry, timezone);

    const footer = (
        <div className={styles.footer}>
            <Button
                type="button"
                variant="secondary"
                onClick={onClose}
            >
                Close
            </Button>

            {entry.task_id && onViewTask && (
                <Button
                    type="button"
                    variant="primary"
                    onClick={() => onViewTask(entry.task_id!)}
                >
                    View in My Tasks
                </Button>
            )}
        </div>
    );

    return (
        <Dialog
            open
            onClose={onClose}
            title="Event details"
            size="md"
            footer={footer}
        >
            <div className={styles.root}>
                <div className={styles.heading}>
                    <div
                        className={cn(
                            styles.iconContainer,
                            styles.eventTypes[entry.event_type],
                        )}
                    >
                        <Icon
                            className={cn(
                                styles.icon,
                                styles.iconTypes[entry.event_type],
                            )}
                            aria-hidden="true"
                        />
                    </div>

                    <div className={styles.headingContent}>
                        <h3
                            className={cn(
                                styles.title,
                                completed && styles.completedTitle,
                            )}
                        >
                            {entry.title}
                        </h3>

                        <span className={styles.eventType}>
                            {eventTypeLabels[entry.event_type]}
                        </span>
                    </div>
                </div>

                <div className={styles.details}>
                    <div className={styles.detailRow}>
                        <CalendarDays
                            className={styles.detailIcon}
                            aria-hidden="true"
                        />

                        <div className={styles.detailContent}>
                            <span className={styles.detailLabel}>
                                Date
                            </span>

                            <span className={styles.detailValue}>
                                {dateDetails.dateLabel}
                            </span>
                        </div>
                    </div>

                    {dateDetails.timeLabel && (
                        <div className={styles.detailRow}>
                            <Clock3
                                className={styles.detailIcon}
                                aria-hidden="true"
                            />

                            <div className={styles.detailContent}>
                                <span className={styles.detailLabel}>
                                    {entry.event_type === "task_deadline"
                                        ? "Due time"
                                        : "Time"}
                                </span>

                                <span className={styles.detailValue}>
                                    {dateDetails.timeLabel}
                                </span>
                            </div>
                        </div>
                    )}

                    {!entry.all_day && (
                        <div className={styles.detailRow}>
                            <Globe2
                                className={styles.detailIcon}
                                aria-hidden="true"
                            />

                            <div className={styles.detailContent}>
                                <span className={styles.detailLabel}>
                                    Display timezone
                                </span>

                                <span className={styles.detailValue}>
                                    {timezone}
                                </span>
                            </div>
                        </div>
                    )}

                    {entry.event_type === "task_deadline" && (
                        <div className={styles.detailRow}>
                            <CheckCircle2
                                className={styles.detailIcon}
                                aria-hidden="true"
                            />

                            <div className={styles.detailContent}>
                                <span className={styles.detailLabel}>
                                    Status
                                </span>

                                <span className={styles.detailValue}>
                                    {entry.status === "completed"
                                        ? "Completed"
                                        : entry.status === "in_progress"
                                            ? "In progress"
                                            : "To do"}
                                </span>
                            </div>
                        </div>
                    )}

                    {entry.priority && (
                        <div className={styles.detailRow}>
                            <Flag
                                className={styles.detailIcon}
                                aria-hidden="true"
                            />

                            <div className={styles.detailContent}>
                                <span className={styles.detailLabel}>
                                    Priority
                                </span>

                                <span className={styles.detailValue}>
                                    {entry.priority.charAt(0).toUpperCase()
                                        + entry.priority.slice(1)}
                                </span>
                            </div>
                        </div>
                    )}
                </div>

                {entry.description && (
                    <div className={styles.descriptionSection}>
                        <h4 className={styles.descriptionHeading}>
                            Description
                        </h4>

                        <p className={styles.description}>
                            {entry.description}
                        </p>
                    </div>
                )}
            </div>
        </Dialog>
    );
}
