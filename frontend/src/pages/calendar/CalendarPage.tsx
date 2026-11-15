import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Temporal } from "temporal-polyfill";
import { CalendarCheck, CalendarDays, CheckCircle2, ChevronLeft, ChevronRight, RefreshCw, Users } from "lucide-react";
import { useNavigate } from "react-router";

import { Button } from "../../components/button";
import { CalendarEventDetailsDialog } from "../../components/calendar/CalendarEventDetailsDialog";
import { CalendarMonthView } from "../../components/calendar/CalendarMonthView";
import { CalendarTimeGrid } from "../../components/calendar/CalendarTimeGrid";
import { PageHeader } from "../../components/page-header/PageHeader";
import { type CalendarEntry, getCalendarEntries } from "../../lib/calendar";
import { getPreferences } from "../../lib/preferences";
import { calendarPageStyles as styles } from "./CalendarPage.styles";
import { getGoogleCalendarStatus, syncGoogleCalendar } from "../../lib/calendar-integrations";
import { toast } from "sonner";

type CalendarView = "month" | "week" | "day";

interface DateRange {
    start: string;
    end: string;
}

const calendarViews: {
    label: string;
    value: CalendarView;
}[] = [
    { label: "Month", value: "month" },
    { label: "Week", value: "week" },
    { label: "Day", value: "day" },
];

function getToday(timezone: string): string {
    return Temporal.Now
        .zonedDateTimeISO(timezone)
        .toPlainDate()
        .toString();
}

function getWeekStart(value: string): Temporal.PlainDate {
    const date = Temporal.PlainDate.from(value);

    return date.subtract({
        days: date.dayOfWeek - 1,
    });
}

function getRange(value: string, view: CalendarView): DateRange {
    const date = Temporal.PlainDate.from(value);

    if (view === "day") {
        return {
            start: value,
            end: date.add({ days: 1 }).toString(),
        };
    }

    if (view === "week") {
        const start = getWeekStart(value);

        return {
            start: start.toString(),
            end: start.add({ days: 7 }).toString(),
        };
    }

    const firstDay = date.with({ day: 1 });
    const lastDay = firstDay.add({ months: 1 }).subtract({ days: 1 });

    const gridStart = getWeekStart(firstDay.toString());
    const gridEnd = lastDay.add({
        days: 8 - lastDay.dayOfWeek,
    });

    return {
        start: gridStart.toString(),
        end: gridEnd.toString(),
    };
}

function getDays(range: DateRange): string[] {
    const days: string[] = [];

    let current = Temporal.PlainDate.from(range.start);
    const end = Temporal.PlainDate.from(range.end);

    while (Temporal.PlainDate.compare(current, end) < 0) {
        days.push(current.toString());
        current = current.add({ days: 1 });
    }

    return days;
}

function formatDate(
    value: string,
    options: Intl.DateTimeFormatOptions,
): string {
    return new Intl.DateTimeFormat("en", {
        ...options,
        timeZone: "UTC",
    }).format(new Date(`${value}T12:00:00Z`));
}

function getCalendarTitle(
    value: string,
    view: CalendarView,
    range: DateRange,
): string {
    if (view === "month") {
        return formatDate(value, {
            month: "long",
            year: "numeric",
        });
    }

    if (view === "day") {
        return formatDate(value, {
            weekday: "long",
            month: "long",
            day: "numeric",
            year: "numeric",
        });
    }

    const lastDay = Temporal.PlainDate
        .from(range.end)
        .subtract({ days: 1 })
        .toString();

    return `${formatDate(range.start, {
        month: "short",
        day: "numeric",
    })} – ${formatDate(lastDay, {
        month: "short",
        day: "numeric",
        year: "numeric",
    })}`;
}

export function Component() {
    const navigate = useNavigate();

    const preferencesQuery = useQuery({
        queryKey: [ "preferences" ],
        queryFn: getPreferences,
    });

    const queryClient = useQueryClient();

    const googleCalendarQuery = useQuery({
        queryKey: [ "calendar-integrations", "google" ],
        queryFn: getGoogleCalendarStatus,
        refetchInterval: (query) => {
            const status = query.state.data;

            if (status?.pending_count || status?.syncing_count) {
                return 3_000;
            }

            return 30_000;
        },
    });

    const syncMutation = useMutation({
        mutationFn: syncGoogleCalendar,

        onSuccess: (result) => {
            void queryClient.invalidateQueries({
                queryKey: [ "calendar-integrations", "google" ],
            });

            toast.success("Calendar synchronization queued", {
                description: `${result.task_count} tasks and ${result.event_count} calendar events queued for synchronization.`,
            });
        },

        onError: (error) => {
            toast.error("Unable to synchronize calendar", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
    });

    const googleStatus = googleCalendarQuery.data;

    const syncInProgress = Boolean(
        googleStatus?.pending_count || googleStatus?.syncing_count,
    );

    const canSync = Boolean(
        googleStatus?.connected
        && !googleCalendarQuery.isError
        && !syncMutation.isPending
        && !syncInProgress,
    );

    const lastSynced = googleStatus?.last_synced_at
        ? new Intl.DateTimeFormat(undefined, {
            dateStyle: "medium",
            timeStyle: "short",
        }).format(new Date(googleStatus.last_synced_at))
        : null;

    const timezone = preferencesQuery.data?.effective_timezone;

    const [ view, setView ] = useState<CalendarView>("month");
    const [ selectedDate, setSelectedDate ] = useState<string | null>(null);
    const [ selectedEvent, setSelectedEvent ] = useState<CalendarEntry | null>(null);

    const anchorDate = selectedDate ?? getToday(timezone ?? "UTC");

    const range = useMemo(
        () => getRange(anchorDate, view),
        [ anchorDate, view ],
    );

    const days = useMemo(
        () => getDays(range),
        [ range ],
    );

    const entriesQuery = useQuery({
        queryKey: [
            "calendar",
            "entries",
            range.start,
            range.end,
            timezone,
        ],
        queryFn: () => getCalendarEntries({
            start: range.start,
            end: range.end,
            timezone: timezone!,
        }),
        enabled: timezone !== undefined,
        staleTime: 60_000,
    });

    const calendarEntries = entriesQuery.data?.entries ?? [];

    const calendarTitle = getCalendarTitle(
        anchorDate,
        view,
        range,
    );

    function navigatePeriod(direction: -1 | 1) {
        const current = Temporal.PlainDate.from(anchorDate);

        const next = view === "month"
            ? current.add({ months: direction })
            : current.add({
                days: view === "week"
                    ? 7 * direction
                    : direction,
            });

        setSelectedDate(next.toString());
    }

    function handleToday() {
        if (timezone) {
            setSelectedDate(getToday(timezone));
        }
    }

    function handleDayClick(day: string) {
        setSelectedDate(day);
        setView("day");
    }

    function handleViewTask(taskId: string) {
        setSelectedEvent(null);

        void navigate("/app/my-tasks", {
            state: { taskId },
        });
    }

    return (
        <main className={styles.root}>

            <PageHeader
                title="Calendar"
                description="View your tasks, deadlines, meetings and appointments."
                actions={
                    googleStatus?.connected ? (
                        <div className={styles.syncActions}>
                            <div className={styles.syncInformation}>
                                <span className={styles.syncDetails}>
                                    {syncInProgress
                                        ? `Synchronizing ${googleStatus.pending_count + googleStatus.syncing_count} changes...`
                                        : googleStatus.failed_count > 0
                                            ? `${googleStatus.failed_count} synchronization failures`
                                            : lastSynced
                                                ? `Last synced: ${lastSynced}`
                                                : "Not synchronized yet"}
                                </span>
                            </div>

                            <Button
                                type="button"
                                variant="secondary"
                                size="sm"
                                disabled={!canSync}
                                onClick={() => syncMutation.mutate()}
                            >
                                <RefreshCw
                                    className={
                                        syncInProgress || syncMutation.isPending
                                            ? "animate-spin"
                                            : undefined
                                    }
                                />

                                {syncMutation.isPending
                                    ? "Queueing..."
                                    : syncInProgress
                                        ? "Syncing..."
                                        : "Sync calendar"}
                            </Button>
                        </div>
                    ) : null
                }
            />

            <section className={styles.calendar}>
                <div className={styles.toolbar}>
                    <div className={styles.navigation}>
                        <Button
                            variant="secondary"
                            size="icon"
                            aria-label="Previous period"
                            onClick={() => navigatePeriod(-1)}
                        >
                            <ChevronLeft/>
                        </Button>

                        <Button
                            variant="secondary"
                            size="icon"
                            aria-label="Next period"
                            onClick={() => navigatePeriod(1)}
                        >
                            <ChevronRight/>
                        </Button>

                        <h2 className={styles.periodTitle}>
                            {calendarTitle}
                        </h2>
                    </div>

                    <div className={styles.toolbarActions}>
                        <Button
                            variant="secondary"
                            size="sm"
                            disabled={!timezone}
                            onClick={handleToday}
                        >
                            <CalendarDays/>
                            Today
                        </Button>

                        <div
                            className={styles.viewSwitch}
                            role="group"
                            aria-label="Calendar view"
                        >
                            {calendarViews.map((option) => (
                                <Button
                                    key={option.value}
                                    variant={view === option.value ? "primary" : "ghost"}
                                    size="sm"
                                    aria-pressed={view === option.value}
                                    onClick={() => setView(option.value)}
                                >
                                    {option.label}
                                </Button>
                            ))}
                        </div>
                    </div>
                </div>

                {preferencesQuery.isError && (
                    <div className={styles.error} role="alert">
                        <span>Unable to load calendar preferences.</span>
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => void preferencesQuery.refetch()}
                        >
                            <RefreshCw/>
                            Retry
                        </Button>
                    </div>
                )}

                {entriesQuery.isError && (
                    <div className={styles.error} role="alert">
                        <span>Unable to load calendar entries.</span>
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => void entriesQuery.refetch()}
                        >
                            <RefreshCw/>
                            Retry
                        </Button>
                    </div>
                )}

                {entriesQuery.isFetching && (
                    <div className={styles.loading} role="status">
                        Loading calendar entries...
                    </div>
                )}

                <div className={styles.calendarBody}>
                    {timezone && (
                        view === "month" ? (
                            <CalendarMonthView
                                date={anchorDate}
                                entries={calendarEntries}
                                timezone={timezone}
                                onDayClick={handleDayClick}
                                onEventClick={setSelectedEvent}
                            />
                        ) : (
                            <CalendarTimeGrid
                                days={days}
                                entries={calendarEntries}
                                timezone={timezone}
                                onDayClick={handleDayClick}
                                onEventClick={setSelectedEvent}
                            />
                        )
                    )}
                </div>
            </section>

            <div className={styles.legend}>
                <span className={styles.legendItem}>
                    <CheckCircle2/>
                    Task deadlines
                </span>

                <span className={styles.legendItem}>
                    <Users/>
                    Meetings
                </span>

                <span className={styles.legendItem}>
                    <CalendarCheck/>
                    Appointments
                </span>
            </div>

            {timezone && (
                <CalendarEventDetailsDialog
                    entry={selectedEvent}
                    timezone={timezone}
                    onClose={() => setSelectedEvent(null)}
                    onViewTask={handleViewTask}
                />
            )}
        </main>
    );
}
