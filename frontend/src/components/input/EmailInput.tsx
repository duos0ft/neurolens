import { type ClipboardEvent, type KeyboardEvent, useState } from "react";
import { X } from "lucide-react";

import { cn } from "../../lib/cn";
import { emailInputStyles as styles } from "./EmailInput.styles";

export interface EmailInputProps {
    values: string[];
    onChange: (values: string[]) => void;
    placeholder?: string;
    disabled?: boolean;
    className?: string;
}

const EMAIL_PATTERN = /^[^\s@,;]+@[^\s@,;]+\.[^\s@,;]+$/;

export function EmailInput({
    values,
    onChange,
    placeholder = "Enter email addresses...",
    disabled = false,
    className,
}: EmailInputProps) {
    const [ input, setInput ] = useState("");
    const [ error, setError ] = useState<string | null>(null);

    function addEmails(text: string) {
        const candidates = text
            .split(/[\s,;]+/)
            .map((email) => email.trim().toLowerCase())
            .filter(Boolean);

        const updated = [ ...values ];
        const invalid: string[] = [];

        for (const email of candidates) {
            if (!EMAIL_PATTERN.test(email)) {
                invalid.push(email);
                continue;
            }

            if (!updated.some((existing) => existing.toLowerCase() === email)) {
                updated.push(email);
            }
        }

        onChange(updated);
        setError(
            invalid.length
                ? `Invalid email address: ${invalid.join(", ")}`
                : null,
        );

        setInput("");
    }

    function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
        if (event.key === "Enter" || event.key === ",") {
            event.preventDefault();

            if (input.trim()) {
                addEmails(input);
            }
        }

        if (event.key === "Backspace" && !input && values.length > 0) {
            onChange(values.slice(0, -1));
        }
    }

    function handlePaste(event: ClipboardEvent<HTMLInputElement>) {
        const text = event.clipboardData.getData("text");

        if (/[\s,;]+/.test(text.trim())) {
            event.preventDefault();
            addEmails(text);
        }
    }

    function removeEmail(email: string) {
        onChange(values.filter((value) => value !== email));
    }

    return (
        <div className={cn(styles.root, className)}>
            <div
                className={cn(styles.field, error && styles.fieldError)}
                onClick={(event) => {
                    if (event.target === event.currentTarget) {
                        event.currentTarget.querySelector("input")?.focus();
                    }
                }}
            >
                {values.map((email) => (
                    <span key={email} className={styles.chip}>
                        <span className={styles.chipText}>{email}</span>

                        <button
                            type="button"
                            disabled={disabled}
                            aria-label={`Remove ${email}`}
                            className={styles.remove}
                            onClick={() => removeEmail(email)}
                        >
                            <X aria-hidden="true"/>
                        </button>
                    </span>
                ))}

                <input
                    type="email"
                    multiple
                    value={input}
                    disabled={disabled}
                    placeholder={values.length ? "Add another email..." : placeholder}
                    onChange={(event) => {
                        setInput(event.target.value);
                        if (error) setError(null);
                    }}
                    onKeyDown={handleKeyDown}
                    onBlur={() => {
                        if (input.trim()) addEmails(input);
                    }}
                    onPaste={handlePaste}
                    className={styles.input}
                    aria-label="Email addresses"
                    aria-invalid={Boolean(error)}
                />
            </div>

            {error && (
                <p className={styles.error} role="alert">
                    {error}
                </p>
            )}
        </div>
    );
}
