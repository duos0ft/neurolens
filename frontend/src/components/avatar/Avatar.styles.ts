import { cva } from "class-variance-authority";

export const avatarVariants = cva(
    "relative inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-muted font-medium text-fg select-none",
    {
        variants: {
            size: {
                sm: "size-7 text-xs",
                md: "size-9 text-sm",
                lg: "size-11 text-base",
                xl: "size-16 text-xl",
            },
        },
        defaultVariants: {
            size: "md",
        },
    },
);
