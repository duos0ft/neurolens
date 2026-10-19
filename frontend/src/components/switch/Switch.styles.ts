export const switchStyles = {
    root: [
        "relative inline-flex h-6 w-11 shrink-0 items-center",
        "rounded-full border border-transparent",
        "bg-muted transition-colors",
        "data-[checked=true]:bg-primary",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    thumb: [
        "pointer-events-none block size-5 rounded-full",
        "bg-white shadow-sm transition-transform",
        "translate-x-0.5",
        "group-data-[checked=true]:translate-x-5",
    ].join(" "),
};
