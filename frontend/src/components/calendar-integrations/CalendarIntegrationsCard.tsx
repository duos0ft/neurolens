import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarDays, RefreshCw, Unplug } from "lucide-react";
import { useSearchParams } from "react-router";

import { Button } from "../button";
import { Card } from "../card";
import { toast } from "../toast";
import {
    connectGoogleCalendar,
    disconnectGoogleCalendar,
    getGoogleCalendarStatus,
} from "../../lib/calendar-integrations";
import { calendarIntegrationsStyles as styles } from "./CalendarIntegrationsCard.styles";

const GOOGLE_QUERY_KEY = [ "calendar-integrations", "google" ];

export function CalendarIntegrationsCard() {
    const queryClient = useQueryClient();
    const [ searchParams, setSearchParams ] = useSearchParams();
    const [ confirmDisconnect, setConfirmDisconnect ] = useState(false);

    const statusQuery = useQuery({
        queryKey: GOOGLE_QUERY_KEY,
        queryFn: getGoogleCalendarStatus,
    });

    const connectMutation = useMutation({
        mutationFn: connectGoogleCalendar,
        onSuccess: ({ authorization_url }) => {
            window.location.assign(authorization_url);
        },
        onError: (error) => {
            toast.error("Unable to connect Google Calendar", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
    });

    const disconnectMutation = useMutation({
        mutationFn: disconnectGoogleCalendar,
        onSuccess: () => {
            setConfirmDisconnect(false);

            void queryClient.invalidateQueries({
                queryKey: GOOGLE_QUERY_KEY,
            });

            void queryClient.invalidateQueries({
                queryKey: [ "calendar" ],
            });

            toast.success("Google Calendar disconnected");
        },
        onError: (error) => {
            toast.error("Unable to disconnect Google Calendar", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
    });

    const googleResult = searchParams.get("google");

    useEffect(() => {
        if (!googleResult) {
            return;
        }

        const messages: Record<string, string> = {
            cancelled: "Google Calendar connection was cancelled.",
            invalid_state: "The connection request expired or was invalid.",
            missing_code: "Google did not return an authorization code.",
            not_configured: "Google Calendar is not configured.",
            insufficient_permissions: "Required calendar permissions were not granted.",
            connection_conflict: "Disconnect your current Google account before connecting a different one.",
            authorization_failed: "Google Calendar authorization failed.",
            connection_failed: "Unable to complete the Google Calendar connection.",
        };

        if (googleResult === "connected") {
            toast.success("Google Calendar connected successfully");
        } else {
            toast.error("Google Calendar connection failed", {
                description: messages[googleResult] ?? "Please try again.",
            });
        }

        void queryClient.invalidateQueries({
            queryKey: GOOGLE_QUERY_KEY,
        });

        setSearchParams((previous) => {
            const updated = new URLSearchParams(previous);
            updated.delete("google");
            return updated;
        }, { replace: true });
    }, [ googleResult, queryClient, setSearchParams ]);

    const connection = statusQuery.data;
    const connected = connection?.connected === true;
    const busy = connectMutation.isPending || disconnectMutation.isPending;

    return (
        <Card variant="flat" padding="lg" className={styles.card}>
            <div className={styles.header}>
                <h2 className={styles.title}>Calendar integrations</h2>
                <p className={styles.description}>
                    Connect an external calendar to bring your schedule
                    into NeuroLens. You stay in control of which events
                    are shared.
                </p>
            </div>

            <div className={styles.divider}/>

            <div className={styles.provider}>
                <div className={styles.providerInfo}>
                    <div className={styles.googleIcon}>
                        <CalendarDays className={styles.icon}/>
                    </div>

                    <div className={styles.providerDetails}>
                        <span className={styles.providerName}>
                            Google Calendar
                        </span>

                        {statusQuery.isPending ? (
                            <span className={styles.providerDescription}>
                                Checking connection...
                            </span>
                        ) : connected ? (
                            <>
                                <span className={styles.connected}>
                                    Connected
                                </span>

                                {connection.account_email && (
                                    <span className={styles.providerDescription}>
                                        {connection.account_email}
                                    </span>
                                )}
                            </>
                        ) : (
                            <span className={styles.providerDescription}>
                                Not connected
                            </span>
                        )}
                    </div>
                </div>

                {!statusQuery.isPending && !statusQuery.isError && (
                    <div className={styles.providerActions}>
                        {connected ? (
                            <Button
                                type="button"
                                variant="secondary"
                                disabled={busy}
                                onClick={() => setConfirmDisconnect(true)}
                            >
                                <Unplug/>
                                Disconnect
                            </Button>
                        ) : (
                            <Button
                                type="button"
                                variant="primary"
                                disabled={busy}
                                onClick={() => connectMutation.mutate()}
                            >
                                {connectMutation.isPending
                                    ? "Connecting..."
                                    : "Connect"}
                            </Button>
                        )}
                    </div>
                )}
            </div>

            {statusQuery.isError && (
                <div className={styles.errorRow}>
                    <span className={styles.error}>
                        Unable to load Google Calendar connection status.
                    </span>

                    <Button
                        type="button"
                        variant="secondary"
                        onClick={() => void statusQuery.refetch()}
                    >
                        <RefreshCw/>
                        Retry
                    </Button>
                </div>
            )}

            {confirmDisconnect && connected && (
                <div className={styles.confirmation}>
                    <div className={styles.confirmationContent}>
                        <h3 className={styles.confirmationTitle}>
                            Disconnect Google Calendar?
                        </h3>

                        <p className={styles.confirmationDescription}>
                            NeuroLens will lose access to this Google account.
                            Your existing NeuroLens tasks and calendar events
                            will not be deleted.
                        </p>
                    </div>

                    <div className={styles.confirmationActions}>
                        <Button
                            type="button"
                            variant="secondary"
                            disabled={disconnectMutation.isPending}
                            onClick={() => setConfirmDisconnect(false)}
                        >
                            Cancel
                        </Button>

                        <Button
                            type="button"
                            variant="primary"
                            disabled={disconnectMutation.isPending}
                            onClick={() => disconnectMutation.mutate()}
                        >
                            {disconnectMutation.isPending
                                ? "Disconnecting..."
                                : "Confirm disconnect"}
                        </Button>
                    </div>
                </div>
            )}

            <div className={styles.divider}/>

            <div className={styles.provider}>
                <div className={styles.providerInfo}>
                    <div className={styles.microsoftIcon}>
                        <CalendarDays className={styles.icon}/>
                    </div>

                    <div className={styles.providerDetails}>
                        <span className={styles.providerName}>
                            Microsoft Outlook
                        </span>
                        <span className={styles.providerDescription}>
                            Microsoft 365 and Outlook calendars
                        </span>
                    </div>
                </div>

                <span className={styles.comingSoon}>
                    Coming later
                </span>
            </div>
        </Card>
    );
}
