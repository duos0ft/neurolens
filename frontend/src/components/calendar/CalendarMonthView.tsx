import { useMemo, useState } from "react";
import { Temporal } from "temporal-polyfill";
import { CalendarCheck, CalendarDays, CheckCircle2, Clock3, Flag, Users } from "lucide-react";

import type { CalendarEntry } from "../../lib/calendar";
import { cn } from "../../lib/cn";
import { calendarMonthViewStyles as styles } from "./CalendarMonthView.styles";

interface CalendarMonthViewProps {
    date: string;
    entries: CalendarEntry[];
    timezone: string;
    onDayClick: (day: string) => void;
    onEventClick: (entry: CalendarEntry) => void;
}

interface DayEvent {
    entry: CalendarEntry;
    timeLabel: string | null;
}

const WEEKDAYS = [
    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
    "Sat",
    "Sun",
];

const MAX_VISIBLE_EVENTS = 2;

function getMonthWeeks(value: string): string[][] {
    const date = Temporal.PlainDate.from(value);
    const firstDay = date.with({ day: 1 });
    const lastDay = firstDay.add({ months: 1 }).subtract({ days: 1 });

    const gridStart = firstDay.subtract({
        days: firstDay.dayOfWeek - 1,
    });

    const gridEnd = lastDay.add({
        days: 7 - lastDay.dayOfWeek,
    });

    const weeks: string[][] = [];
    let current = gridStart;

    while (Temporal.PlainDate.compare(current, gridEnd) <= 0) {
        const week: string[] = [];

        for (let index = 0; index < 7; index++) {
            week.push(current.toString());
            current = current.add({ days: 1 });
        }

        weeks.push(week);
    }

    return weeks;
}

function formatTime(hour: number, minute: number): string {
    return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

function getDayEvents(
    entries: CalendarEntry[],
    day: string,
    timezone: string,
): DayEvent[] {
    const start = Temporal.PlainDate
        .from(day)
        .toZonedDateTime({
            timeZone: timezone,
            plainTime: "00:00",
        })
        .toInstant();

    const end = Temporal.PlainDate
        .from(day)
        .add({ days: 1 })
        .toZonedDateTime({
            timeZone: timezone,
            plainTime: "00:00",
        })
        .toInstant();

    const dayEvents: DayEvent[] = [];

    for (const entry of entries) {
        if (entry.all_day) {
            if (
                entry.start_date
                && entry.end_date
                && entry.start_date <= day
                && entry.end_date > day
            ) {
                dayEvents.push({
                    entry,
                    timeLabel: null,
                });
            }

            continue;
        }

        if (!entry.starts_at || !entry.ends_at) {
            continue;
        }

        const eventStart = Temporal.Instant.from(entry.starts_at);
        const eventEnd = Temporal.Instant.from(entry.ends_at);

        if (
            Temporal.Instant.compare(eventStart, end) >= 0
            || Temporal.Instant.compare(eventEnd, start) <= 0
        ) {
            continue;
        }

        const localStart = eventStart.toZonedDateTimeISO(timezone);

        dayEvents.push({
            entry,
            timeLabel: localStart.toPlainDate().toString() === day
                ? formatTime(localStart.hour, localStart.minute)
                : "Continues",
        });
    }

    dayEvents.sort((a, b) => {
        if (a.entry.all_day !== b.entry.all_day) {
            return a.entry.all_day ? -1 : 1;
        }

        if (a.entry.all_day) {
            return a.entry.title.localeCompare(b.entry.title);
        }

        return a.entry.starts_at!.localeCompare(
            b.entry.starts_at!,
        );
    });

    return dayEvents;
}

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
        case "event":
            return CalendarDays;
        default:
            return Clock3;
    }
}

function MonthEvent({
    item,
    onClick,
}: {
    item: DayEvent;
    onClick: (entry: CalendarEntry) => void;
}) {
    const { entry, timeLabel } = item;
    const Icon = getEventIcon(entry.event_type);

    const completed = entry.event_type === "task_deadline"
        && entry.status === "completed";

    return (
        <button
            type="button"
            className={cn(
                styles.event,
                styles.eventTypes[entry.event_type],
                completed && styles.eventCompleted,
            )}
            title={entry.title}
            onClick={() => onClick(entry)}
        >
            <Icon
                className={cn(
                    styles.eventIcon,
                    styles.eventIconTypes[entry.event_type],
                    completed && styles.eventCompletedIcon,
                )}
                aria-hidden="true"
            />

            <span className={styles.eventContent}>
                <span
                    className={cn(
                        styles.eventTitle,
                        completed && styles.eventCompletedTitle,
                    )}
                >
                    {entry.title}
                </span>

                {timeLabel && (
                    <span className={styles.eventTime}>
                        {timeLabel}
                    </span>
                )}
            </span>
        </button>
    );
}

export function CalendarMonthView({
    date,
    entries,
    timezone,
    onDayClick,
    onEventClick,
}: CalendarMonthViewProps) {
    const [ expandedDays, setExpandedDays ] = useState<Set<string>>(
        () => new Set(),
    );

    const weeks = useMemo(
        () => getMonthWeeks(date),
        [ date ],
    );

    const today = Temporal.Now
        .zonedDateTimeISO(timezone)
        .toPlainDate()
        .toString();

    const currentMonth = Temporal.PlainDate.from(date).month;

    const dayEvents = useMemo(() => {
        const result = new Map<string, DayEvent[]>();

        for (const week of weeks) {
            for (const day of week) {
                result.set(
                    day,
                    getDayEvents(entries, day, timezone),
                );
            }
        }

        return result;
    }, [ weeks, entries, timezone ]);

    function toggleExpanded(day: string) {
        setExpandedDays((previous) => {
            const next = new Set(previous);

            if (next.has(day)) {
                next.delete(day);
            } else {
                next.add(day);
            }

            return next;
        });
    }

    return (
        <div className={styles.root}>
            <div className={styles.scroll}>
                <div className={styles.content}>
                    <div className={styles.weekdays}>
                        {WEEKDAYS.map((weekday) => (
                            <div
                                key={weekday}
                                className={styles.weekday}
                            >
                                {weekday}
                            </div>
                        ))}
                    </div>

                    <div className={styles.weeks}>
                        {weeks.map((week) => (
                            <div
                                key={week[0]}
                                className={styles.week}
                            >
                                {week.map((day) => {
                                    const parsedDay = Temporal.PlainDate.from(day);
                                    const isToday = day === today;
                                    const isOutside = parsedDay.month !== currentMonth;

                                    const events = dayEvents.get(day) ?? [];
                                    const expanded = expandedDays.has(day);

                                    const visibleEvents = expanded
                                        ? events
                                        : events.slice(0, MAX_VISIBLE_EVENTS);

                                    const hiddenCount = events.length - visibleEvents.length;

                                    return (
                                        <div
                                            key={day}
                                            className={cn(
                                                styles.day,
                                                isOutside && styles.dayOutside,
                                                isToday && styles.dayToday,
                                            )}
                                        >
                                            <div className={styles.dayHeader}>
                                                <button
                                                    type="button"
                                                    className={cn(
                                                        styles.dayButton,
                                                        isOutside && styles.dayButtonOutside,
                                                        isToday && styles.dayButtonToday,
                                                    )}
                                                    onClick={() => onDayClick(day)}
                                                    aria-label={`Open ${day}`}
                                                    aria-current={
                                                        isToday ? "date" : undefined
                                                    }
                                                >
                                                    {parsedDay.day}
                                                </button>
                                            </div>

                                            <div className={styles.dayEvents}>
                                                {visibleEvents.map((item) => (
                                                    <MonthEvent
                                                        key={item.entry.id}
                                                        item={item}
                                                        onClick={onEventClick}
                                                    />
                                                ))}

                                                {hiddenCount > 0 && (
                                                    <button
                                                        type="button"
                                                        className={styles.moreButton}
                                                        onClick={() => toggleExpanded(day)}
                                                        aria-expanded={false}
                                                    >
                                                        +{hiddenCount} more
                                                    </button>
                                                )}

                                                {expanded && events.length > MAX_VISIBLE_EVENTS && (
                                                    <button
                                                        type="button"
                                                        className={styles.moreButton}
                                                        onClick={() => toggleExpanded(day)}
                                                        aria-expanded={true}
                                                    >
                                                        Show less
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
