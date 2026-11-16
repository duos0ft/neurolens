export function normalizePolicyCitations(content: string): string {
    return content.replace(
        /\[((?:P\d+\s*,\s*)+P\d+)\]/g,
        (_match, group: string) =>
            group
                .split(/\s*,\s*/)
                .map((reference) => `[${reference}]`)
                .join(" "),
    );
}
