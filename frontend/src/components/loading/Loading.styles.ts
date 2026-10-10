import { cva } from "class-variance-authority";

export const loadingStyles = {
    root: "flex flex-col items-center justify-center gap-5",
    spinner: cva("animate-spin rounded-full border-solid border-muted border-t-accent motion-reduce:animate-none", {
        variants: {
            size: {
                sm: "size-5 border-2",
                md: "size-8 border-2",
                lg: "size-12 border-[3px]",
                xl: "size-16 border-[3px]",
            },
        },
        defaultVariants: {
            size: "md",
        },
    }),
    content: "flex flex-col items-center gap-1.5 text-center",
    title: "text-title font-medium text-fg",
    description: "text-sm text-fg-muted",
};
