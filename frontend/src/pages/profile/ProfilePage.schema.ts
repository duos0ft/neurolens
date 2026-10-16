import { z } from "zod";

const optionalText = (maxLength: number) =>
    z.string().trim().max(maxLength, `Must be ${maxLength} characters or fewer`);

export const profileSchema = z.object({
    display_name: optionalText(100),
    job_title: optionalText(150),
    department: optionalText(150),
    team: optionalText(150),
});

export type ProfileFormValues = z.infer<typeof profileSchema>;
