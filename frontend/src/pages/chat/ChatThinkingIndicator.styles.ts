export const chatThinkingIndicatorStyles = {
    root: [
        "mx-auto flex w-full max-w-content",
        "items-start gap-4",
    ].join(" "),

    orb: [
        "mt-1 size-8 shrink-0 rounded-full",
        "bg-orb shadow-orb",
        "animate-breathe",
        "motion-reduce:animate-none",
        "[[data-reduce-motion=true]_&]:animate-none",
    ].join(" "),

    content: [
        "flex min-w-0 flex-1 flex-col",
        "items-start gap-2",
    ].join(" "),

    label: [
        "text-eyebrow font-medium uppercase",
        "tracking-eyebrow text-fg-muted",
    ].join(" "),

    status: [
        "text-sm text-fg-soft",
    ].join(" "),

    skeleton: [
        "mt-2 flex w-full max-w-xs",
        "flex-col gap-2.5",
        "animate-pulse",
        "motion-reduce:animate-none",
        "[[data-reduce-motion=true]_&]:animate-none",
    ].join(" "),

    skeletonLong: [
        "h-2 w-4/5 rounded-full bg-muted",
    ].join(" "),

    skeletonShort: [
        "h-2 w-1/2 rounded-full bg-muted",
    ].join(" "),
};
