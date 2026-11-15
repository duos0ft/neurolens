import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Controller, useForm } from "react-hook-form";

import { Button } from "../../components/button";
import { Card } from "../../components/card";
import { PageHeader } from "../../components/page-header/PageHeader";
import { Select } from "../../components/select/Select";
import { Switch } from "../../components/switch";
import { toast } from "../../components/toast";
import { getPreferences, updatePreferences } from "../../lib/preferences";
import { getTimezoneOptions } from "../../lib/timezones";
import { defaultPreferences, type PreferencesFormValues, preferencesSchema } from "./PreferencesPage.schema";
import { preferencesPageStyles as styles } from "./PreferencesPage.styles";

const directnessOptions = [
    { label: "Gentle", value: "low" },
    { label: "Balanced", value: "balanced" },
    { label: "Direct", value: "high" },
] as const;

const responseLengthOptions = [
    { label: "Short", value: "short" },
    { label: "Medium", value: "medium" },
    { label: "Detailed", value: "detailed" },
] as const;

const INHERIT_TIMEZONE = "__organization_default__";

export function Component() {
    const queryClient = useQueryClient();

    const preferencesQuery = useQuery({
        queryKey: [ "preferences" ],
        queryFn: getPreferences,
    });

    const {
        control,
        handleSubmit,
        reset,
        formState: { isDirty, isSubmitting, errors },
    } = useForm<PreferencesFormValues>({
        resolver: zodResolver(preferencesSchema),
        defaultValues: defaultPreferences,
    });

    useEffect(() => {
        if (preferencesQuery.data && !isDirty) {
            reset({
                directness: preferencesQuery.data.directness,
                response_length: preferencesQuery.data.response_length,
                highlight_ambiguity: preferencesQuery.data.highlight_ambiguity,
                step_by_step_guidance: preferencesQuery.data.step_by_step_guidance,
                always_show_next_step: preferencesQuery.data.always_show_next_step,
                timezone: preferencesQuery.data.timezone,
            });
        }
    }, [ preferencesQuery.data, isDirty, reset ]);

    const mutation = useMutation({
        mutationFn: updatePreferences,

        onSuccess: (preferences) => {
            queryClient.setQueryData(
                [ "preferences" ],
                preferences,
            );

            reset({
                directness: preferences.directness,
                response_length: preferences.response_length,
                highlight_ambiguity: preferences.highlight_ambiguity,
                step_by_step_guidance: preferences.step_by_step_guidance,
                always_show_next_step: preferences.always_show_next_step,
                timezone: preferences.timezone,
            });

            void queryClient.invalidateQueries({
                queryKey: [ "calendar" ],
            });

            toast.success("Preferences updated", {
                description: "NeuroLens will use your preferences for future responses.",
            });
        },

        onError: (error) => {
            toast.error("Unable to save preferences", {
                description: error instanceof Error
                    ? error.message
                    : "Something went wrong. Please try again.",
            });
        },
    });

    function onSubmit(values: PreferencesFormValues) {
        mutation.mutate(values);
    }

    if (preferencesQuery.isPending) {
        return (
            <div className={styles.root}>
                <p className={styles.description}>
                    Loading preferences...
                </p>
            </div>
        );
    }

    if (preferencesQuery.isError) {
        return (
            <div className={styles.root}>
                <p className={styles.error} role="alert">
                    Unable to load your preferences. Please try again.
                </p>

                <div>
                    <Button
                        variant="secondary"
                        onClick={() => void preferencesQuery.refetch()}
                    >
                        Try again
                    </Button>
                </div>
            </div>
        );
    }

    return (
        <div className={styles.root}>
            <PageHeader
                title="Preferences"
                description="Personalize how NeuroLens communicates and guides you."
            />

            <Card variant="flat" padding="lg" className={styles.card}>
                <form
                    className={styles.form}
                    onSubmit={handleSubmit(onSubmit)}
                    noValidate
                >
                    <section className={styles.section}>
                        <div className={styles.sectionHeader}>
                            <h2 className={styles.sectionTitle}>
                                Communication style
                            </h2>

                            <p className={styles.sectionDescription}>
                                Choose how NeuroLens explains information to you.
                            </p>
                        </div>

                        <div className={styles.field}>
                            <label className={styles.label}>
                                Directness
                            </label>

                            <p className={styles.hint}>
                                Adjust how straightforward the responses should be.
                            </p>

                            <div className={styles.selectWrapper}>
                                <Controller
                                    name="directness"
                                    control={control}
                                    render={({ field }) => (
                                        <Select
                                            options={[ ...directnessOptions ]}
                                            value={field.value}
                                            onChange={(value) => {
                                                if (value !== null) {
                                                    field.onChange(value);
                                                }
                                            }}
                                            placeholder="Directness"
                                            disabled={mutation.isPending}
                                        />
                                    )}
                                />
                            </div>
                        </div>

                        <div className={styles.field}>
                            <label className={styles.label}>
                                Response length
                            </label>

                            <p className={styles.hint}>
                                Choose how much detail you want in AI responses.
                            </p>

                            <div className={styles.selectWrapper}>
                                <Controller
                                    name="response_length"
                                    control={control}
                                    render={({ field }) => (
                                        <Select
                                            options={[ ...responseLengthOptions ]}
                                            value={field.value}
                                            onChange={(value) => {
                                                if (value !== null) {
                                                    field.onChange(value);
                                                }
                                            }}
                                            placeholder="Response length"
                                            disabled={mutation.isPending}
                                        />
                                    )}
                                />
                            </div>
                        </div>
                    </section>

                    <div className={styles.divider}/>

                    <section className={styles.section}>
                        <div className={styles.sectionHeader}>
                            <h2 className={styles.sectionTitle}>
                                Guidance and clarity
                            </h2>

                            <p className={styles.sectionDescription}>
                                Customize how NeuroLens helps you understand
                                instructions and plan your next action.
                            </p>
                        </div>

                        <div className={styles.switchRow}>
                            <div className={styles.switchInfo}>
                                <span className={styles.label}>
                                    Highlight ambiguity
                                </span>

                                <p className={styles.hint}>
                                    Identify unclear instructions or missing information.
                                </p>
                            </div>

                            <Controller
                                name="highlight_ambiguity"
                                control={control}
                                render={({ field }) => (
                                    <Switch
                                        checked={field.value}
                                        onChange={field.onChange}
                                        disabled={mutation.isPending}
                                        aria-label="Highlight ambiguity"
                                    />
                                )}
                            />
                        </div>

                        <div className={styles.switchRow}>
                            <div className={styles.switchInfo}>
                                <span className={styles.label}>
                                    Step-by-step guidance
                                </span>

                                <p className={styles.hint}>
                                    Break complicated instructions into manageable steps.
                                </p>
                            </div>

                            <Controller
                                name="step_by_step_guidance"
                                control={control}
                                render={({ field }) => (
                                    <Switch
                                        checked={field.value}
                                        onChange={field.onChange}
                                        disabled={mutation.isPending}
                                        aria-label="Step-by-step guidance"
                                    />
                                )}
                            />
                        </div>

                        <div className={styles.switchRow}>
                            <div className={styles.switchInfo}>
                                <span className={styles.label}>
                                    Always show next step
                                </span>

                                <p className={styles.hint}>
                                    Suggest a clear, actionable next step when appropriate.
                                </p>
                            </div>

                            <Controller
                                name="always_show_next_step"
                                control={control}
                                render={({ field }) => (
                                    <Switch
                                        checked={field.value}
                                        onChange={field.onChange}
                                        disabled={mutation.isPending}
                                        aria-label="Always show next step"
                                    />
                                )}
                            />
                        </div>
                    </section>

                    <div className={styles.divider}/>

                    <section className={styles.section}>
                        <div className={styles.sectionHeader}>
                            <h2 className={styles.sectionTitle}>
                                Date and time
                            </h2>

                            <p className={styles.sectionDescription}>
                                Choose how NeuroLens interprets and displays
                                your meetings, appointments, and deadlines.
                            </p>
                        </div>

                        <div className={styles.field}>
                            <label className={styles.label}>
                                My timezone
                            </label>

                            <p className={styles.hint}>
                                Use your organization's default timezone,
                                or choose a different timezone for yourself.
                            </p>

                            <div className={styles.selectWrapper}>
                                <Controller
                                    name="timezone"
                                    control={control}
                                    render={({ field }) => (
                                        <Select<string>
                                            options={[
                                                {
                                                    label: "Use organization default",
                                                    value: INHERIT_TIMEZONE,
                                                },
                                                ...getTimezoneOptions(field.value),
                                            ]}
                                            value={
                                                field.value ?? INHERIT_TIMEZONE
                                            }
                                            onChange={(value) => {
                                                field.onChange(
                                                    value === INHERIT_TIMEZONE
                                                        ? null
                                                        : value,
                                                );
                                            }}
                                            placeholder="Select your timezone"
                                            disabled={mutation.isPending}
                                        />
                                    )}
                                />
                            </div>

                            {errors.timezone && (
                                <p className={styles.error} role="alert">
                                    {errors.timezone.message}
                                </p>
                            )}

                            <p className={styles.hint}>
                                Current effective timezone:{" "}
                                <strong className="font-medium text-fg">
                                    {preferencesQuery.data.effective_timezone}
                                </strong>
                            </p>

                            <p className={styles.hint}>
                                Changing your timezone affects how
                                upcoming calendar events and deadlines
                                are displayed. It does not change the
                                actual time of existing meetings.
                            </p>
                        </div>
                    </section>

                    <div className={styles.divider}/>

                    <div className={styles.actions}>
                        <Button
                            variant="primary"
                            type="submit"
                            disabled={
                                !isDirty
                                || isSubmitting
                                || mutation.isPending
                            }
                        >
                            {mutation.isPending
                                ? "Saving..."
                                : "Save changes"}
                        </Button>
                    </div>
                </form>
            </Card>
        </div>
    );
}
