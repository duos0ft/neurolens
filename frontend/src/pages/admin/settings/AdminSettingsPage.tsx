import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Controller, useForm } from "react-hook-form";

import { Button } from "../../../components/button";
import { Card } from "../../../components/card";
import { Input } from "../../../components/input";
import { Switch } from "../../../components/switch";
import { toast } from "../../../components/toast";
import { getApplicationSettings, updateApplicationSettings } from "../../../lib/application-settings";
import { type AdminSettingsFormValues, adminSettingsSchema, defaultAdminSettings } from "./AdminSettingsPage.schema";
import { adminSettingsPageStyles as styles } from "./AdminSettingsPage.styles";
import { PageHeader } from "../../../components/page-header/PageHeader";
import { Select } from "../../../components/select/Select";
import { getTimezoneOptions } from "../../../lib/timezones";

export function Component() {
    const queryClient = useQueryClient();

    const settingsQuery = useQuery({
        queryKey: [ "application-settings" ],
        queryFn: getApplicationSettings,
    });

    const {
        control,
        register,
        handleSubmit,
        reset,
        formState: { errors, isDirty },
    } = useForm<AdminSettingsFormValues>({
        resolver: zodResolver(adminSettingsSchema),
        mode: "onBlur",
        defaultValues: defaultAdminSettings,
    });

    useEffect(() => {
        if (settingsQuery.data && !isDirty) {
            reset({
                organization_name: settingsQuery.data.organization_name,
                default_timezone: settingsQuery.data.default_timezone,
                enable_task_assistance: settingsQuery.data.enable_task_assistance,
                enable_policy_assistance: settingsQuery.data.enable_policy_assistance,
                enable_sentiment_analysis: settingsQuery.data.enable_sentiment_analysis,
            });
        }
    }, [ settingsQuery.data, isDirty, reset ]);

    const mutation = useMutation({
        mutationFn: updateApplicationSettings,
        onSuccess: (settings) => {
            queryClient.setQueryData([ "application-settings" ], settings);

            reset({
                organization_name: settings.organization_name,
                default_timezone: settings.default_timezone,
                enable_task_assistance: settings.enable_task_assistance,
                enable_policy_assistance: settings.enable_policy_assistance,
                enable_sentiment_analysis: settings.enable_sentiment_analysis,
            });

            toast.success("Settings updated", {
                description: "Application settings have been saved successfully.",
            });
        },
        onError: (error) => {
            toast.error("Unable to save settings", {
                description: error instanceof Error
                    ? error.message
                    : "Something went wrong. Please try again.",
            });
        },
    });

    function onSubmit(values: AdminSettingsFormValues) {
        mutation.mutate(values);
    }

    if (settingsQuery.isPending) {
        return (
            <div className={styles.root}>
                <PageHeader
                    title="Admin settings"
                    description="Manage application-wide configuration for NeuroLens."
                />
                <p className={styles.hint}>Loading settings...</p>
            </div>
        );
    }

    if (settingsQuery.isError) {
        return (
            <div className={styles.root}>
                <PageHeader
                    title="Admin settings"
                    description="Manage application-wide configuration for NeuroLens."
                />

                <p className={styles.error} role="alert">
                    Unable to load application settings. Please try again.
                </p>

                <div>
                    <Button
                        variant="secondary"
                        onClick={() => void settingsQuery.refetch()}
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
                title="Admin settings"
                description="Manage application-wide configuration for NeuroLens."
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
                                General settings
                            </h2>
                            <p className={styles.sectionDescription}>
                                Configure how your organization is represented in NeuroLens.
                            </p>
                        </div>

                        <div className={styles.field}>
                            <label
                                className={styles.label}
                                htmlFor="organization-name"
                            >
                                Organization name
                            </label>

                            <Input
                                id="organization-name"
                                placeholder="Organization name"
                                maxLength={150}
                                disabled={mutation.isPending}
                                aria-invalid={Boolean(errors.organization_name)}
                                aria-describedby={
                                    errors.organization_name
                                        ? "organization-name-error"
                                        : undefined
                                }
                                {...register("organization_name")}
                            />

                            {errors.organization_name && (
                                <p
                                    id="organization-name-error"
                                    className={styles.error}
                                    role="alert"
                                >
                                    {errors.organization_name.message}
                                </p>
                            )}
                        </div>

                        <div className={styles.field}>
                            <label className={styles.label}>
                                Organization default timezone
                            </label>

                            <p className={styles.hint}>
                                Used for employees who haven't selected their own timezone.
                                This also affects how NeuroLens interprets new meetings
                                and deadlines.
                            </p>

                            <div className={styles.selectWrapper}>
                                <Controller
                                    name="default_timezone"
                                    control={control}
                                    render={({ field }) => (
                                        <Select<string>
                                            options={getTimezoneOptions(field.value)}
                                            value={field.value}
                                            onChange={(value) => {
                                                if (value !== null) {
                                                    field.onChange(value);
                                                }
                                            }}
                                            placeholder="Select organization timezone"
                                            disabled={mutation.isPending}
                                        />
                                    )}
                                />
                            </div>

                            {errors.default_timezone && (
                                <p className={styles.error} role="alert">
                                    {errors.default_timezone.message}
                                </p>
                            )}
                        </div>

                    </section>

                    <div className={styles.divider}/>

                    <section className={styles.section}>
                        <div className={styles.sectionHeader}>
                            <h2 className={styles.sectionTitle}>
                                AI capabilities
                            </h2>
                            <p className={styles.sectionDescription}>
                                Choose which AI-assisted features are enabled
                                for employees in your organization.
                            </p>
                        </div>

                        <div className={styles.switchRow}>
                            <div className={styles.switchInfo}>
                                <span className={styles.label}>
                                    Task assistance
                                </span>
                                <p className={styles.hint}>
                                    Help employees extract tasks and break
                                    complex work into manageable steps.
                                </p>
                            </div>

                            <Controller
                                name="enable_task_assistance"
                                control={control}
                                render={({ field }) => (
                                    <Switch
                                        checked={field.value}
                                        onChange={field.onChange}
                                        disabled={mutation.isPending}
                                        aria-label="Enable task assistance"
                                    />
                                )}
                            />
                        </div>

                        <div className={styles.switchRow}>
                            <div className={styles.switchInfo}>
                                <span className={styles.label}>
                                    Policy assistance
                                </span>
                                <p className={styles.hint}>
                                    Allow employees to ask questions about
                                    organizational policies and procedures.
                                </p>
                            </div>

                            <Controller
                                name="enable_policy_assistance"
                                control={control}
                                render={({ field }) => (
                                    <Switch
                                        checked={field.value}
                                        onChange={field.onChange}
                                        disabled={mutation.isPending}
                                        aria-label="Enable policy assistance"
                                    />
                                )}
                            />
                        </div>

                        <div className={styles.switchRow}>
                            <div className={styles.switchInfo}>
                                <span className={styles.label}>
                                    Sentiment analysis
                                </span>
                                <p className={styles.hint}>
                                    Enable experimental sentiment classification
                                    using the configured NLP model.
                                </p>
                            </div>

                            <Controller
                                name="enable_sentiment_analysis"
                                control={control}
                                render={({ field }) => (
                                    <Switch
                                        checked={field.value}
                                        onChange={field.onChange}
                                        disabled={mutation.isPending}
                                        aria-label="Enable sentiment analysis"
                                    />
                                )}
                            />
                        </div>
                    </section>

                    <div className={styles.divider}/>

                    <div className={styles.actions}>
                        <Button
                            variant="primary"
                            type="submit"
                            disabled={!isDirty || mutation.isPending}
                        >
                            {mutation.isPending ? "Saving..." : "Save changes"}
                        </Button>
                    </div>
                </form>
            </Card>
        </div>
    );
}
