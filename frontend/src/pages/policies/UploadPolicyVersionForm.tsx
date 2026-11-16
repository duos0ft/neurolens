import { useMutation } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { DatePicker } from "../../components/date-picker/DatePicker";
import { toast } from "../../components/toast";
import { type PolicyVersion, uploadPolicyVersion } from "../../lib/policies";
import { uploadPolicyVersionFormStyles as styles } from "./UploadPolicyVersionForm.styles";
import { FileUpload } from "../../components/file-upload/FileUpload";

interface UploadPolicyVersionFormProps {
    documentId: string;
    formId: string;
    onUploaded: (version: PolicyVersion) => void;
    onPendingChange: (pending: boolean) => void;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024;

const uploadPolicyVersionSchema = z.object({
    file: z
        .file({ error: "Please select a PDF document." })
        .refine(
            (file) =>
                file.type === "application/pdf"
                || file.name.toLowerCase().endsWith(".pdf"),
            "Only PDF documents are supported.",
        )
        .max(MAX_FILE_SIZE, "The PDF must not exceed 10 MB."),
    effectiveDate: z.string().nullable(),
});

type UploadPolicyVersionFormInput = z.input<
    typeof uploadPolicyVersionSchema
>;

type UploadPolicyVersionFormValues = z.infer<
    typeof uploadPolicyVersionSchema
>;

export function UploadPolicyVersionForm({
    documentId,
    formId,
    onUploaded,
    onPendingChange,
}: UploadPolicyVersionFormProps) {

    const {
        control,
        handleSubmit,
        formState: { errors },
    } = useForm<
        UploadPolicyVersionFormInput,
        unknown,
        UploadPolicyVersionFormValues
    >({
        resolver: zodResolver(uploadPolicyVersionSchema),
        defaultValues: {
            effectiveDate: null,
        },
        mode: "onSubmit",
    });

    const uploadMutation = useMutation({
        mutationFn: uploadPolicyVersion,
        onSuccess: (version) => {
            toast.success("Policy PDF uploaded successfully.");
            onUploaded(version);
        },
        onError: (error) => {
            toast.error("Unable to upload policy PDF.", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
        onSettled: () => {
            onPendingChange(false);
        },
    });

    function onSubmit(values: UploadPolicyVersionFormValues) {
        if (uploadMutation.isPending) {
            return;
        }

        onPendingChange(true);

        uploadMutation.mutate({
            documentId,
            file: values.file,
            effectiveDate: values.effectiveDate,
        });
    }

    return (
        <form
            id={formId}
            className={styles.form}
            onSubmit={handleSubmit(onSubmit)}
            noValidate
        >
            <div className={styles.field}>
                <label
                    htmlFor={`${formId}-file`}
                    className={styles.label}
                >
                    PDF document
                </label>

                <Controller
                    name="file"
                    control={control}
                    render={({ field, fieldState }) => (
                        <FileUpload
                            value={field.value ?? null}
                            onChange={field.onChange}
                            onBlur={field.onBlur}
                            accept=".pdf,application/pdf"
                            maxSizeMB={10}
                            disabled={uploadMutation.isPending}
                            error={fieldState.error?.message}
                        />
                    )}
                />
            </div>

            <div className={styles.field}>
                <label
                    htmlFor={`${formId}-date`}
                    className={styles.label}
                >
                    Effective date
                </label>

                <Controller
                    name="effectiveDate"
                    control={control}
                    render={({ field }) => (
                        <DatePicker
                            id={`${formId}-date`}
                            value={field.value}
                            onChange={field.onChange}
                            disabled={uploadMutation.isPending}
                            clearable
                        />
                    )}
                />

                <p className={styles.hint}>
                    Optional. The date from which this policy version takes effect.
                </p>

                {errors.effectiveDate && (
                    <p className={styles.error} role="alert">
                        {errors.effectiveDate.message}
                    </p>
                )}
            </div>
        </form>
    );
}
