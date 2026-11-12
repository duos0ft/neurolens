export const timezoneOptions = [
    { label: "UTC", value: "UTC" },
    { label: "Cyprus — Asia/Nicosia", value: "Asia/Nicosia" },
    { label: "Netherlands — Europe/Amsterdam", value: "Europe/Amsterdam" },
    { label: "United Kingdom — Europe/London", value: "Europe/London" },
    { label: "Germany — Europe/Berlin", value: "Europe/Berlin" },
    { label: "Greece — Europe/Athens", value: "Europe/Athens" },
    { label: "Moldova — Europe/Chisinau", value: "Europe/Chisinau" },
    { label: "United States — America/New_York", value: "America/New_York" },
    { label: "United States — America/Chicago", value: "America/Chicago" },
    { label: "United States — America/Los_Angeles", value: "America/Los_Angeles" },
    { label: "UAE — Asia/Dubai", value: "Asia/Dubai" },
    { label: "Japan — Asia/Tokyo", value: "Asia/Tokyo" },
] as const;

export function getTimezoneOptions(
    currentTimezone?: string | null,
): { label: string; value: string }[] {
    const options: { label: string; value: string }[] = [
        ...timezoneOptions,
    ];

    if (
        currentTimezone
        && !options.some((option) => option.value === currentTimezone)
    ) {
        options.push({
            label: currentTimezone,
            value: currentTimezone,
        });
    }

    return options;
}
