import { useEffect, useMemo, useRef, useState } from "react";
import { Temporal } from "temporal-polyfill";
import { CalendarCheck, CheckCircle2, Clock3, Users } from "lucide-react";

import type { CalendarEntry } from "../../lib/calendar";
import { cn } from "../../lib/cn";
import { calendarTimeGridStyles as styles } from "./CalendarTimeGrid.styles";

interface CalendarTimeGridProps {
    days: string[];
    entries: CalendarEntry[];
    timezone: string;
    onEventClick?: (entry: CalendarEntry) => void;
    onDayClick?: (day: string) => void;
}

interface PositionedEvent {
    entry: CalendarEntry;
    top: number;
    height: number;
    lane: number;
    lanes: number;
    timeLabel: string;
    isDeadline: boolean;
    markerTop: number;
}

interface CurrentTime {
    date: string;
    hour: number;
    minute: number;
}

const HOUR_HEIGHT = 64;
const MAX_VISIBLE_ALL_DAY_EVENTS = 2;
const DAY_HEIGHT = 24 * HOUR_HEIGHT;
const MIN_EVENT_HEIGHT = 32;

const HOURS = Array.from({ length: 24 }, (_, index) => index);

function getCurrentTime(timezone: string): CurrentTime {
    const now = Temporal.Now.zonedDateTimeISO(timezone);

    return {
        date: now.toPlainDate().toString(),
        hour: now.hour,
        minute: now.minute,
    };
}

function formatHour(hour: number): string {
    return `${String(hour).padStart(2, "0")}:00`;
}

function formatTime(hour: number, minute: number): string {
    return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

function getDayLabel(value: string) {
    const date = Temporal.PlainDate.from(value);

    const weekday = new Intl.DateTimeFormat("en", {
        weekday: "short",
        timeZone: "UTC",
    }).format(new Date(`${value}T12:00:00Z`));

    return {
        weekday,
        number: date.day,
    };
}

function getIcon(type: CalendarEntry["event_type"]) {
    switch (type) {
        case "task_deadline":
            return CheckCircle2;
        case "meeting":
            return Users;
        case "appointment":
            return CalendarCheck;
        default:
            return Clock3;
    }
}

function getAllDayEvents(
    entries: CalendarEntry[],
    day: string,
): CalendarEntry[] {
    return entries.filter((entry) =>
        entry.all_day
        && entry.start_date !== null
        && entry.end_date !== null
        && entry.start_date <= day
        && entry.end_date > day,
    );
}

function getTimedEvents(
    entries: CalendarEntry[],
    day: string,
    timezone: string,
): PositionedEvent[] {
    const dayStart = Temporal.PlainDate
        .from(day)
        .toZonedDateTime({
            timeZone: timezone,
            plainTime: "00:00",
        })
        .toInstant();

    const dayEnd = Temporal.PlainDate
        .from(day)
        .add({ days: 1 })
        .toZonedDateTime({
            timeZone: timezone,
            plainTime: "00:00",
        })
        .toInstant();

    const positioned: PositionedEvent[] = [];

    for (const entry of entries) {
        if (
            entry.all_day
            || !entry.starts_at
            || !entry.ends_at
        ) {
            continue;
        }

        const startInstant = Temporal.Instant.from(entry.starts_at);
        const endInstant = Temporal.Instant.from(entry.ends_at);

        if (
            Temporal.Instant.compare(startInstant, dayEnd) >= 0
            || Temporal.Instant.compare(endInstant, dayStart) <= 0
        ) {
            continue;
        }

        const start = startInstant.toZonedDateTimeISO(timezone);
        const end = endInstant.toZonedDateTimeISO(timezone);

        const startDay = start.toPlainDate().toString();
        const endDay = end.toPlainDate().toString();

        const startMinute = day === startDay
            ? start.hour * 60 + start.minute + start.second / 60
            : 0;

        const endMinute = day === endDay
            ? end.hour * 60 + end.minute + end.second / 60
            : 1440;

        if (endMinute <= startMinute) {
            continue;
        }

        const isDeadline = entry.event_type === "task_deadline"
            || entry.event_type === "deadline";

        const duration = Math.max(
            0,
            endMinute - startMinute,
        ) / 60 * HOUR_HEIGHT;

        const height = isDeadline
            ? 72
            : Math.max(duration, MIN_EVENT_HEIGHT);

        const actualTop = startMinute / 60 * HOUR_HEIGHT;

        const top = isDeadline
            ? Math.max(0, Math.min(
                actualTop - height - 6,
                DAY_HEIGHT - height,
            ))
            : Math.max(0, Math.min(
                actualTop,
                DAY_HEIGHT - height,
            ));

        positioned.push({
            entry,
            top,
            height,
            lane: 0,
            lanes: 1,
            timeLabel: formatTime(start.hour, start.minute),
            isDeadline,
            markerTop: Math.min(actualTop, DAY_HEIGHT - 2),
        });
    }

    positioned.sort(
        (a, b) => a.top - b.top || b.height - a.height,
    );

    let group: PositionedEvent[] = [];
    let groupEnd = 0;

    function finishGroup() {
        const occupiedUntil: number[] = [];

        for (const event of group) {
            let lane = occupiedUntil.findIndex(
                (end) => end <= event.top,
            );

            if (lane === -1) {
                lane = occupiedUntil.length;
                occupiedUntil.push(0);
            }

            event.lane = lane;
            occupiedUntil[lane] = event.top + event.height;
        }

        for (const event of group) {
            event.lanes = occupiedUntil.length;
        }

        group = [];
        groupEnd = 0;
    }

    for (const event of positioned) {
        if (group.length && event.top >= groupEnd) {
            finishGroup();
        }

        group.push(event);
        groupEnd = Math.max(groupEnd, event.top + event.height);
    }

    if (group.length) {
        finishGroup();
    }

    return positioned;
}

function EventCard({
    entry,
    timeLabel,
    compact = false,
    onClick,
}: {
    entry: CalendarEntry;
    timeLabel?: string;
    compact?: boolean;
    onClick?: (entry: CalendarEntry) => void;
}) {
    const Icon = getIcon(entry.event_type);
    const completed = entry.event_type === "task_deadline"
        && entry.status === "completed";

    const isDeadline = entry.event_type === "task_deadline"
        || entry.event_type === "deadline";

    const className = cn(
        styles.event,
        styles.eventTypes[entry.event_type],
        isDeadline && styles.eventDeadline,
        compact && styles.eventCompact,
        completed && styles.eventCompleted,
        "w-full",
        onClick && "cursor-pointer",
    );

    const content = (
        <>
            <Icon
                className={cn(
                    styles.eventIcon,
                    styles.eventIconTypes[entry.event_type],
                    completed && styles.eventCompletedIcon,
                )}
                aria-hidden="true"
            />

            <div className={styles.eventDetails}>

                <span
                    className={cn(
                        styles.eventTitle,
                        compact && styles.eventCompactTitle,
                        isDeadline && styles.eventDeadlineTitle,
                        completed && styles.eventCompletedTitle,
                    )}
                >
                    {entry.title}
                </span>

                {!compact && timeLabel && (
                    <span className={styles.eventTime}>
                        {timeLabel}
                    </span>
                )}
            </div>
        </>
    );

    if (onClick) {
        return (
            <button
                type="button"
                className={cn(
                    className,
                    "w-full text-left transition-colors duration-150",
                    "hover:brightness-95",
                    "focus-visible:outline-2 focus-visible:outline-offset-2",
                )}
                title={entry.title}
                onClick={() => onClick(entry)}
            >
                {content}
            </button>
        );
    }

    return (
        <div className={className} title={entry.title}>
            {content}
        </div>
    );
}

export function CalendarTimeGrid({
    days,
    entries,
    timezone,
    onEventClick,
    onDayClick,
}: CalendarTimeGridProps) {
    const scrollRef = useRef<HTMLDivElement>(null);

    const [ currentTime, setCurrentTime ] = useState<CurrentTime>(
        () => getCurrentTime(timezone),
    );

    const [ expandedDays, setExpandedDays ] = useState<Set<string>>(
        () => new Set(),
    );

    function toggleExpandedDay(day: string) {
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

    const columns = `52px repeat(${days.length}, minmax(0, 1fr))`;

    const allDayEvents = useMemo(
        () => days.map((day) => getAllDayEvents(entries, day)),
        [ days, entries ],
    );

    const timedEvents = useMemo(
        () => days.map((day) =>
            getTimedEvents(entries, day, timezone),
        ),
        [ days, entries, timezone ],
    );

    const visibleDateKey = days.join(",");

    const currentTimeTop = (
        currentTime.hour * 60 + currentTime.minute
    ) / 60 * HOUR_HEIGHT;

    useEffect(() => {
        setCurrentTime(getCurrentTime(timezone));

        const interval = window.setInterval(() => {
            setCurrentTime(getCurrentTime(timezone));
        }, 30_000);

        return () => window.clearInterval(interval);
    }, [ timezone ]);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = 8 * HOUR_HEIGHT;
        }
    }, [ visibleDateKey ]);

    return (
        <div className={styles.root}>
            <div className="overflow-x-auto">
                <div className={cn(
                    days.length > 1 && "min-w-[760px]",
                )}>
                    <div
                        className={styles.header}
                        style={{ gridTemplateColumns: columns }}
                    >
                        <div/>

                        {days.map((day) => {
                            const label = getDayLabel(day);
                            const isToday = day === currentTime.date;

                            return (
                                <div
                                    key={day}
                                    className={styles.dayHeading}
                                >
                                    <button
                                        type="button"
                                        className={cn(
                                            styles.dayHeadingButton,
                                            isToday && styles.dayHeadingToday,
                                            !onDayClick && "cursor-default",
                                        )}
                                        onClick={() => onDayClick?.(day)}
                                        disabled={!onDayClick}
                                        aria-label={`Open ${label.weekday}, ${day}`}
                                        aria-current={
                                            isToday ? "date" : undefined
                                        }
                                    >
                                        <span className={styles.dayHeadingWeekday}>
                                            {label.weekday}
                                        </span>

                                        <span className={cn(
                                            isToday && styles.todayNumber,
                                        )}>
                                            {label.number}
                                        </span>
                                    </button>
                                </div>
                            );
                        })}
                    </div>

                    <div
                        className={styles.allDay}
                        style={{ gridTemplateColumns: columns }}
                    >
                        <div className={styles.allDayLabel}>
                            All-day
                        </div>

                        {days.map((day, index) => {
                            const dayEvents = allDayEvents[index];
                            const expanded = expandedDays.has(day);

                            const visibleEvents = expanded
                                ? dayEvents
                                : dayEvents.slice(0, MAX_VISIBLE_ALL_DAY_EVENTS);

                            const hiddenCount = dayEvents.length - visibleEvents.length;

                            return (
                                <div
                                    key={day}
                                    className={cn(
                                        styles.allDayColumn,
                                        day === currentTime.date
                                        && styles.allDayToday,
                                    )}
                                >
                                    {visibleEvents.map((entry) => (
                                        <EventCard
                                            key={entry.id}
                                            entry={entry}
                                            compact
                                            onClick={onEventClick}
                                        />
                                    ))}

                                    {hiddenCount > 0 && (
                                        <button
                                            type="button"
                                            className={styles.allDayMore}
                                            onClick={() => toggleExpandedDay(day)}
                                            aria-expanded={expanded}
                                        >
                                            +{hiddenCount} more
                                        </button>
                                    )}

                                    {expanded && dayEvents.length > MAX_VISIBLE_ALL_DAY_EVENTS && (
                                        <button
                                            type="button"
                                            className={styles.allDayMore}
                                            onClick={() => toggleExpandedDay(day)}
                                            aria-expanded={true}
                                        >
                                            Show less
                                        </button>
                                    )}
                                </div>
                            );
                        })}
                    </div>

                    <div
                        ref={scrollRef}
                        className={styles.timelineScroll}
                    >
                        <div
                            className={styles.timeline}
                            style={{ gridTemplateColumns: columns }}
                        >
                            <div
                                className={styles.hours}
                                style={{ height: DAY_HEIGHT }}
                            >
                                {HOURS.map((hour) => (
                                    <span
                                        key={hour}
                                        className={cn(
                                            styles.hour,
                                            hour === 0
                                                ? "translate-y-0"
                                                : "-translate-y-1/2",
                                        )}
                                        style={{
                                            top: hour === 0
                                                ? 6
                                                : hour * HOUR_HEIGHT,
                                        }}

                                    >
                                        {formatHour(hour)}
                                    </span>
                                ))}

                                {days.includes(currentTime.date) && (
                                    <span
                                        className={styles.currentTimeLabel}
                                        style={{ top: currentTimeTop }}
                                    >
                                        {formatTime(
                                            currentTime.hour,
                                            currentTime.minute,
                                        )}
                                    </span>
                                )}
                            </div>

                            {days.map((day, index) => (
                                <div
                                    key={day}
                                    className={cn(
                                        styles.dayColumn,
                                        day === currentTime.date
                                        && styles.dayColumnToday,
                                    )}
                                    style={{ height: DAY_HEIGHT }}
                                >

                                    {timedEvents[index].map((event) => (
                                        <div key={event.entry.id}>
                                            <div
                                                className={styles.positionedEvent}
                                                style={{
                                                    top: event.top,
                                                    height: event.height,
                                                    left: `calc(${event.lane} * 100% / ${event.lanes} + 3px)`,
                                                    width: `calc(100% / ${event.lanes} - 6px)`,
                                                }}
                                            >
                                                <EventCard
                                                    entry={event.entry}
                                                    timeLabel={event.timeLabel}
                                                    compact={
                                                        !event.isDeadline
                                                        && event.height < 44
                                                    }
                                                    onClick={onEventClick}
                                                />
                                            </div>
                                        </div>
                                    ))}

                                    {day === currentTime.date && (
                                        <div
                                            className={styles.currentTimeLine}
                                            style={{ top: currentTimeTop }}
                                            aria-hidden="true"
                                        >
                                            <span
                                                className={styles.currentTimeDot}
                                            />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
