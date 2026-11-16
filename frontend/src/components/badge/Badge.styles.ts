export const badgeStyles = {
    root: [
        "inline-flex w-fit shrink-0 items-center",
        "rounded-full px-2.5 py-1",
        "text-xs font-medium leading-none",
        "whitespace-nowrap",
    ].join(" "),

    variants: {
        neutral: [
            "bg-muted text-fg-muted",
        ].join(" "),

        success: [
            "bg-emerald-50 text-emerald-700",
            "dark:bg-emerald-950 dark:text-emerald-300",
        ].join(" "),

        warning: [
            "bg-amber-50 text-amber-700",
            "dark:bg-amber-950 dark:text-amber-300",
        ].join(" "),

        danger: [
            "bg-red-50 text-red-700",
            "dark:bg-red-950 dark:text-red-300",
        ].join(" "),
    },
};
