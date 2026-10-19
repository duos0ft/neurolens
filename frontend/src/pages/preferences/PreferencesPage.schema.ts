import { z } from "zod";

export const preferencesSchema = z.object({
    directness: z.enum([ "low", "balanced", "high" ]),
    response_length: z.enum([ "short", "medium", "detailed" ]),
    highlight_ambiguity: z.boolean(),
    step_by_step_guidance: z.boolean(),
    always_show_next_step: z.boolean(),
});

export type PreferencesFormValues = z.infer<typeof preferencesSchema>;

export const defaultPreferences: PreferencesFormValues = {
    directness: "balanced",
    response_length: "medium",
    highlight_ambiguity: true,
    step_by_step_guidance: true,
    always_show_next_step: true,
};
