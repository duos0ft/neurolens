import { cva } from "class-variance-authority";

export const buttonVariants = cva(
    [
        "inline-flex shrink-0 items-center justify-center gap-2",
        "rounded-lg font-medium transition-colors",
        "disabled:pointer-events-none disabled:opacity-50",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
        "[&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
    ],
    {
        variants: {
            variant: {
                primary: "bg-primary text-on-primary hover:bg-primary-hover",
                secondary: "border border-border bg-bg text-fg hover:bg-muted",
                ghost: "text-fg hover:bg-muted",
                destructive: "bg-destructive text-on-destructive hover:bg-destructive-hover",
            },
            size: {
                sm: "h-8 px-3 text-xs",
                md: "h-10 px-4 text-sm",
                lg: "h-11 px-5 text-sm",
                icon: "size-9",
            },
        },
        defaultVariants: {
            variant: "secondary",
            size: "md",
        },
    },
);
