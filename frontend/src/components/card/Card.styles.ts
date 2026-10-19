import { cva } from "class-variance-authority";

export const cardVariants = cva("rounded-lg border border-border bg-surface text-fg", {
    variants: {
        variant: {
            default: "shadow-sm",
            flat: "shadow-none",
            elevated: "shadow-lg",
        },
        padding: {
            none: "p-0",
            sm: "p-4",
            md: "p-6",
            lg: "p-8",
        },
    },
    defaultVariants: {
        variant: "default",
        padding: "md",
    },
});
