import { cva } from "class-variance-authority";

export const inputVariants = cva(
    [
        "flex w-full min-w-0 rounded-lg border border-border bg-bg text-fg",
        "transition-colors outline-none",
        "placeholder:text-fg-muted",
        "focus-visible:border-border-strong focus-visible:ring-0",
        "disabled:cursor-not-allowed disabled:opacity-50",
        "aria-invalid:border-neg-fg aria-invalid:ring-2 aria-invalid:ring-neg-fg/15",
    ],
    {
        variants: {
            inputSize: {
                sm: "h-9 px-3 text-sm",
                md: "h-10 px-3 text-sm",
                lg: "h-11 px-4 text-base",
            },
        },
        defaultVariants: {
            inputSize: "md",
        },
    },
);
