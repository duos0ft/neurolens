import { z } from "zod";

export const adminSettingsSchema = z.object({
    organization_name: z.string()
        .trim()
        .min(1, "Organization name is required.")
        .max(150, "Organization name cannot exceed 150 characters."),

    enable_task_assistance: z.boolean(),
    enable_policy_assistance: z.boolean(),
    enable_sentiment_analysis: z.boolean(),
});

export type AdminSettingsFormValues = z.infer<typeof adminSettingsSchema>;

export const defaultAdminSettings: AdminSettingsFormValues = {
    organization_name: "NeuroLens",
    enable_task_assistance: true,
    enable_policy_assistance: true,
    enable_sentiment_analysis: false,
};
