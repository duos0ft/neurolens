import { type ComponentRef, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import FullCalendar from "@fullcalendar/react";
import classicThemePlugin from "@fullcalendar/react/themes/classic";
import dayGridPlugin from "@fullcalendar/react/daygrid";
import timeGridPlugin from "@fullcalendar/react/timegrid";
import interactionPlugin from "@fullcalendar/react/interaction";
import {
    CalendarCheck,
    CalendarDays,
    CheckCircle2,
    ChevronLeft,
    ChevronRight,
    Clock3,
    RefreshCw,
    Users,
} from "lucide-react";
import { useNavigate } from "react-router";

import "@fullcalendar/react/skeleton.css";
import "@fullcalendar/react/themes/classic/theme.css";
import "@fullcalendar/react/themes/classic/palette.css";
import "./CalendarPage.css";

import { Button } from "../../components/button";
import { PageHeader } from "../../components/page-header/PageHeader";
import { type CalendarEntry, getCalendarEntries } from "../../lib/calendar";
import { calendarPageStyles as styles } from "./CalendarPage.styles";

type CalendarView = "dayGridMonth" | "timeGridWeek" | "timeGridDay";

interface DateRange {
    start: string;
    end: string;
}

const calendarPlugins = [
    classicThemePlugin,
    dayGridPlugin,
    timeGridPlugin,
    interactionPlugin,
];

const calendarViews: {
    label: string;
    value: CalendarView;
}[] = [
    { label: "Month", value: "dayGridMonth" },
    { label: "Week", value: "timeGridWeek" },
    { label: "Day", value: "timeGridDay" },
];

function getCalendarTimezone(): string {
    return Intl.DateTimeFormat()
        .resolvedOptions()
        .timeZone || "UTC";
}

function mapCalendarEntry(entry: CalendarEntry) {
    return {
        id: entry.id,
        title: entry.title,
        start: entry.all_day
            ? entry.start_date!
            : entry.starts_at!,
        end: entry.all_day
            ? entry.end_date!
            : entry.ends_at!,
        allDay: entry.all_day,
        extendedProps: {
            source: entry.source,
            eventType: entry.event_type,
            taskId: entry.task_id,
            status: entry.status,
            priority: entry.priority,
        },
    };
}

function CalendarEventContent({
    title,
    eventType,
    completed,
}: {
    title: string;
    eventType: CalendarEntry["event_type"];
    completed: boolean;
}) {
    const Icon = eventType === "task_deadline"
        ? CheckCircle2
        : eventType === "meeting"
            ? Users
            : eventType === "appointment"
                ? CalendarCheck
                : Clock3;

    return (
        <span
            className={[
                styles.eventContent,
                completed && styles.eventCompleted,
            ].filter(Boolean).join(" ")}
            title={title}
        >
            <Icon
                className={styles.eventIcon}
                aria-hidden="true"
            />

            <span className={styles.eventTitle}>
                {title}
            </span>
        </span>
    );
}

export function Component() {
    const navigate = useNavigate();
    const calendarRef = useRef<ComponentRef<typeof FullCalendar>>(null);

    const [ view, setView ] = useState<CalendarView>("dayGridMonth");
    const [ calendarTitle, setCalendarTitle ] = useState("");
    const [ range, setRange ] = useState<DateRange | null>(null);

    const timezone = useMemo(
        () => getCalendarTimezone(),
        [],
    );

    const entriesQuery = useQuery({
        queryKey: [
            "calendar",
            "entries",
            range?.start,
            range?.end,
            timezone,
        ],
        queryFn: () => getCalendarEntries({
            start: range!.start,
            end: range!.end,
            timezone,
        }),
        enabled: range !== null,
        staleTime: 60_000,
    });

    const entries = useMemo(
        () => (entriesQuery.data?.entries ?? []).map(mapCalendarEntry),
        [ entriesQuery.data ],
    );

    function handleViewChange(nextView: CalendarView) {
        calendarRef.current?.getApi().changeView(nextView);
    }

    function handlePrevious() {
        calendarRef.current?.getApi().prev();
    }

    function handleNext() {
        calendarRef.current?.getApi().next();
    }

    function handleToday() {
        calendarRef.current?.getApi().today();
    }

    return (
        <main className={styles.root}>
            <PageHeader
                title="Calendar"
                description="View your tasks, deadlines, meetings and appointments."
            />

            <section className={styles.calendar}>
                <div className={styles.toolbar}>
                    <div className={styles.navigation}>
                        <Button
                            variant="secondary"
                            size="icon"
                            aria-label="Previous period"
                            onClick={handlePrevious}
                        >
                            <ChevronLeft/>
                        </Button>

                        <Button
                            variant="secondary"
                            size="icon"
                            aria-label="Next period"
                            onClick={handleNext}
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
                                    variant={
                                        view === option.value
                                            ? "primary"
                                            : "ghost"
                                    }
                                    size="sm"
                                    aria-pressed={view === option.value}
                                    onClick={() => {
                                        handleViewChange(option.value);
                                    }}
                                >
                                    {option.label}
                                </Button>
                            ))}
                        </div>
                    </div>
                </div>

                {entriesQuery.isError && (
                    <div className={styles.error} role="alert">
                        <span>Unable to load calendar entries.</span>

                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => {
                                void entriesQuery.refetch();
                            }}
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
                    <FullCalendar
                        ref={calendarRef}
                        plugins={calendarPlugins}
                        initialView="dayGridMonth"
                        headerToolbar={false}
                        timeZone={timezone}
                        firstDay={1}
                        height="auto"
                        fixedWeekCount={false}
                        showNonCurrentDates
                        dayMaxEvents={3}
                        nowIndicator
                        navLinks
                        editable={false}
                        selectable={false}
                        events={entries}
                        datesSet={(info) => {
                            setCalendarTitle(info.view.title);
                            setView(info.view.type as CalendarView);

                            const nextRange = {
                                start: info.startStr.slice(0, 10),
                                end: info.endStr.slice(0, 10),
                            };

                            setRange((previous) =>
                                previous?.start === nextRange.start
                                && previous?.end === nextRange.end
                                    ? previous
                                    : nextRange,
                            );
                        }}
                        eventContent={(info) => (
                            <CalendarEventContent
                                title={info.event.title}
                                eventType={info.event.extendedProps.eventType}
                                completed={
                                    info.event.extendedProps.status === "completed"
                                }
                            />
                        )}
                        eventClick={(info) => {
                            const taskId = info.event.extendedProps.taskId;

                            if (taskId) {
                                void navigate("/app/my-tasks");
                            }
                        }}
                        dayHeaderFormat={{
                            weekday: "short",
                        }}
                        slotMinTime="06:00:00"
                        slotMaxTime="22:00:00"
                        slotDuration="00:30:00"
                        allDaySlot
                        expandRows
                    />
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
        </main>
    );
}
