import type { ChangeEvent, DragEvent } from "react";
import { useId, useRef, useState } from "react";
import { CheckCircle2, FileText, FileUp, X } from "lucide-react";

import { Button } from "../button";
import { cn } from "../../lib/cn";
import { fileUploadStyles as styles } from "./FileUpload.styles";

interface FileUploadProps {
    value: File | null;
    onChange: (file: File | null) => void;
    onBlur?: () => void;
    accept?: string;
    disabled?: boolean;
    error?: string;
    maxSizeMB?: number;
}

function formatFileSize(bytes: number): string {
    if (bytes < 1024 * 1024) {
        return `${(bytes / 1024).toFixed(1)} KB`;
    }

    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileUpload({
    value,
    onChange,
    onBlur,
    accept = ".pdf,application/pdf",
    disabled = false,
    error,
    maxSizeMB = 10,
}: FileUploadProps) {
    const inputId = useId();
    const inputRef = useRef<HTMLInputElement>(null);
    const [ dragging, setDragging ] = useState(false);

    function handleFile(file: File | null) {
        if (disabled) {
            return;
        }

        onChange(file);
        onBlur?.();
    }

    function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
        handleFile(event.target.files?.[0] ?? null);
    }

    function handleDragOver(event: DragEvent<HTMLDivElement>) {
        event.preventDefault();

        if (!disabled) {
            event.dataTransfer.dropEffect = "copy";
            setDragging(true);
        }
    }

    function handleDragLeave(event: DragEvent<HTMLDivElement>) {
        event.preventDefault();

        if (!event.currentTarget.contains(event.relatedTarget as Node)) {
            setDragging(false);
        }
    }

    function handleDrop(event: DragEvent<HTMLDivElement>) {
        event.preventDefault();
        setDragging(false);

        if (disabled) {
            return;
        }

        const files = event.dataTransfer.files;

        if (files.length === 1) {
            handleFile(files[0]);
        } else if (files.length > 1) {
            handleFile(null);
        }
    }

    function handleRemove() {
        if (inputRef.current) {
            inputRef.current.value = "";
        }

        handleFile(null);
    }

    return (
        <div className={styles.root}>
            <input
                ref={inputRef}
                id={inputId}
                type="file"
                accept={accept}
                disabled={disabled}
                onChange={handleInputChange}
                onBlur={onBlur}
                aria-invalid={Boolean(error)}
                aria-describedby={error ? `${inputId}-error` : undefined}
                className={styles.input}
            />

            {value ? (
                <div className={cn(
                    styles.selectedFile,
                    error && styles.errorBorder,
                )}>
                    <div className={styles.fileIcon}>
                        <FileText aria-hidden="true"/>
                    </div>

                    <div className={styles.fileDetails}>
                        <span className={styles.fileName}>
                            {value.name}
                        </span>

                        <span className={styles.fileMeta}>
                            {formatFileSize(value.size)}
                            {" · "}
                            <CheckCircle2
                                className={styles.checkIcon}
                                aria-hidden="true"
                            />
                            Selected
                        </span>
                    </div>

                    <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        disabled={disabled}
                        aria-label="Remove selected file"
                        onClick={handleRemove}
                    >
                        <X aria-hidden="true"/>
                    </Button>
                </div>
            ) : (
                <div
                    className={cn(
                        styles.dropzone,
                        dragging && styles.dragging,
                        error && styles.errorBorder,
                        disabled && styles.disabled,
                    )}
                    onDragEnter={(event) => {
                        event.preventDefault();

                        if (!disabled) {
                            setDragging(true);
                        }
                    }}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                >
                    <div className={styles.uploadIcon}>
                        <FileUp aria-hidden="true"/>
                    </div>

                    <div className={styles.uploadText}>
                        <p className={styles.uploadTitle}>
                            Drop your file here
                        </p>

                        <p className={styles.uploadDescription}>
                            or choose a file from your computer
                        </p>
                    </div>

                    <label
                        htmlFor={inputId}
                        className={cn(
                            styles.browseButton,
                            disabled && styles.disabled,
                        )}
                    >
                        Choose file
                    </label>

                    <span className={styles.hint}>
                        Maximum file size: {maxSizeMB} MB
                    </span>
                </div>
            )}

            {error && (
                <p
                    id={`${inputId}-error`}
                    className={styles.error}
                    role="alert"
                >
                    {error}
                </p>
            )}
        </div>
    );
}
