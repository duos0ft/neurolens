export const checkboxStyles = {
    root: [
        "inline-flex min-w-0 items-start gap-2.5",
        "cursor-pointer select-none",
    ].join(" "),

    disabled: "cursor-not-allowed opacity-50",

    control: "group/checkbox relative mt-0.5 flex size-4 shrink-0",

    input: [
        "peer absolute inset-0 z-10 m-0 size-full",
        "cursor-inherit opacity-0",
    ].join(" "),

    box: [
        "flex size-4 items-center justify-center",
        "rounded-[4px] border border-border-strong",
        "bg-bg text-white",
        "transition-colors duration-150",

        "peer-hover:border-fg-muted",
        "peer-focus-visible:outline-2",
        "peer-focus-visible:outline-offset-2",
        "peer-focus-visible:outline-ring",

        "peer-checked:border-primary",
        "peer-checked:bg-primary",

        "peer-aria-checked:border-primary",
        "peer-aria-checked:bg-primary",
    ].join(" "),

    icon: [
        "size-3 stroke-[3] opacity-0",
        "group-has-[:checked]/checkbox:opacity-100",
        "group-aria-[checked=mixed]/checkbox:opacity-100",
    ].join(" "),

    content: "flex min-w-0 flex-col gap-1",

    label: "text-sm font-medium text-fg",

    description: "text-xs leading-5 text-fg-muted",
};
