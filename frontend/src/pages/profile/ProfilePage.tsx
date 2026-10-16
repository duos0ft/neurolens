import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Avatar } from "../../components/avatar";
import { Button } from "../../components/button";
import { Card } from "../../components/card";
import { Input } from "../../components/input";
import { useAuth } from "../../providers/AuthProvider";
import { profileSchema, type ProfileFormValues } from "./ProfilePage.schema";
import { profilePageStyles as styles } from "./ProfilePage.styles";

export function Component() {
    const { employee } = useAuth();

    const {
        register,
        handleSubmit,
        reset,
        formState: { errors, isDirty, isSubmitting },
    } = useForm<ProfileFormValues>({
        resolver: zodResolver(profileSchema),
        mode: "onBlur",
        defaultValues: {
            display_name: employee?.display_name ?? "",
            job_title: employee?.job_title ?? "",
            department: employee?.department ?? "",
            team: employee?.team ?? "",
        },
    });

    useEffect(() => {
        reset({
            display_name: employee?.display_name ?? "",
            job_title: employee?.job_title ?? "",
            department: employee?.department ?? "",
            team: employee?.team ?? "",
        });
    }, [employee, reset]);

    const name = employee?.display_name || employee?.email || "My profile";
    const subtitle = employee?.job_title || "NeuroLens employee";

    function onSubmit(values: ProfileFormValues) {
        // PATCH /api/profile will be connected next.
        // Do not treat this as a successful save yet.
        console.log("Validated profile fields", Object.keys(values));
    }

    return (
        <div className={styles.root}>
            <header className={styles.header}>
                <h1 className={styles.title}>My profile</h1>
                <p className={styles.description}>Manage your personal information and workplace details.</p>
            </header>

            <Card variant="flat" padding="lg" className={styles.profileCard}>
                <div className={styles.profileHeader}>
                    <Avatar name={name} size="xl" />

                    <div className={styles.profileInfo}>
                        <h2 className={styles.profileName}>{name}</h2>
                        <p className={styles.profileSubtitle}>{subtitle}</p>
                    </div>
                </div>

                <div className={styles.divider} />

                <div className={styles.sectionHeader}>
                    <h2 className={styles.sectionTitle}>Personal information</h2>
                    <p className={styles.sectionDescription}>
                        Your profile helps coworkers recognize you within NeuroLens.
                    </p>
                </div>

                <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
                    <div className={styles.fields}>
                        <div className={styles.field}>
                            <label className={styles.label} htmlFor="profile-display-name">
                                Display name
                            </label>
                            <Input
                                id="profile-display-name"
                                placeholder="Your full name"
                                aria-invalid={Boolean(errors.display_name)}
                                aria-describedby={errors.display_name ? "display-name-error" : undefined}
                                {...register("display_name")}
                            />
                            {errors.display_name && (
                                <p id="display-name-error" className={styles.error} role="alert">
                                    {errors.display_name.message}
                                </p>
                            )}
                        </div>

                        <div className={styles.field}>
                            <label className={styles.label} htmlFor="profile-email">
                                Email address
                            </label>
                            <Input id="profile-email" value={employee?.email ?? ""} disabled readOnly />
                            <p className={styles.hint}>Managed through your NeuroLens account.</p>
                        </div>

                        <div className={styles.field}>
                            <label className={styles.label} htmlFor="profile-job-title">
                                Job title
                            </label>
                            <Input
                                id="profile-job-title"
                                placeholder="e.g. Software Engineer"
                                aria-invalid={Boolean(errors.job_title)}
                                aria-describedby={errors.job_title ? "job-title-error" : undefined}
                                {...register("job_title")}
                            />
                            {errors.job_title && (
                                <p id="job-title-error" className={styles.error} role="alert">
                                    {errors.job_title.message}
                                </p>
                            )}
                        </div>

                        <div className={styles.field}>
                            <label className={styles.label} htmlFor="profile-department">
                                Department
                            </label>
                            <Input
                                id="profile-department"
                                placeholder="e.g. Engineering"
                                aria-invalid={Boolean(errors.department)}
                                aria-describedby={errors.department ? "department-error" : undefined}
                                {...register("department")}
                            />
                            {errors.department && (
                                <p id="department-error" className={styles.error} role="alert">
                                    {errors.department.message}
                                </p>
                            )}
                        </div>

                        <div className={styles.field}>
                            <label className={styles.label} htmlFor="profile-team">
                                Team
                            </label>
                            <Input
                                id="profile-team"
                                placeholder="e.g. Platform"
                                aria-invalid={Boolean(errors.team)}
                                aria-describedby={errors.team ? "team-error" : undefined}
                                {...register("team")}
                            />
                            {errors.team && (
                                <p id="team-error" className={styles.error} role="alert">
                                    {errors.team.message}
                                </p>
                            )}
                        </div>
                    </div>

                    <div className={styles.actions}>
                        <Button variant="primary" type="submit" disabled={!isDirty || isSubmitting}>
                            Save changes
                        </Button>
                    </div>
                </form>
            </Card>
        </div>
    );
}
