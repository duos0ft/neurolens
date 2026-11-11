import { useMutation } from "@tanstack/react-query";
import { type SubmitEvent, useEffect, useId, useState } from "react";
import { toast } from "sonner";

import { Button } from "../../../components/button";
import { Dialog } from "../../../components/dialog";
import { Input } from "../../../components/input";
import {
    type ContactPerson,
    type ContactPersonInput,
    createContactPerson,
    updateContactPerson,
    type UpdateContactPersonInput,
} from "../../../lib/contact-persons";

import { contactPersonDialogStyles as styles } from "./ContactPersonDialog.styles";

interface ContactPersonDialogProps {
    open: boolean;
    contact: ContactPerson | null;
    onClose: () => void;
    onSaved: () => void;
}

export function ContactPersonDialog({
    open,
    contact,
    onClose,
    onSaved,
}: ContactPersonDialogProps) {
    const formId = useId();
    const isEditing = contact !== null;

    const [ name, setName ] = useState("");
    const [ email, setEmail ] = useState("");
    const [ jobTitle, setJobTitle ] = useState("");
    const [ department, setDepartment ] = useState("");
    const [ responsibility, setResponsibility ] = useState("");
    const [ isPrimary, setIsPrimary ] = useState(false);

    const saveMutation = useMutation({
        mutationFn: (payload: ContactPersonInput) => {
            if (contact) {
                const updatePayload: UpdateContactPersonInput = {
                    ...payload,
                    is_active: contact.is_active,
                };

                return updateContactPerson(contact.id, updatePayload);
            }

            return createContactPerson(payload);
        },
    });

    useEffect(() => {
        if (!open) {
            return;
        }

        setName(contact?.name ?? "");
        setEmail(contact?.email ?? "");
        setJobTitle(contact?.job_title ?? "");
        setDepartment(contact?.department ?? "");
        setResponsibility(contact?.responsibility ?? "");
        setIsPrimary(contact?.is_primary ?? false);

        saveMutation.reset();
    }, [ open, contact, saveMutation ]);

    function closeDialog() {
        if (saveMutation.isPending) {
            return;
        }

        onClose();
    }

    async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
        event.preventDefault();

        if (
            saveMutation.isPending
            || !name.trim()
            || !email.trim()
            || !responsibility.trim()
        ) {
            return;
        }

        const payload: ContactPersonInput = {
            name: name.trim().replace(/\s+/g, " "),
            email: email.trim().toLowerCase(),
            job_title: jobTitle.trim() || null,
            department: department.trim() || null,
            responsibility: responsibility.trim().replace(/\s+/g, " "),
            is_primary: isPrimary,
        };

        try {
            await saveMutation.mutateAsync(payload);

            toast.success(
                isEditing
                    ? "Contact person updated successfully."
                    : "Contact person added successfully.",
            );

            onSaved();
            onClose();
        } catch (error) {
            toast.error(
                isEditing
                    ? "Unable to update contact person."
                    : "Unable to add contact person.",
                {
                    description: error instanceof Error
                        ? error.message
                        : "Please try again.",
                },
            );
        }
    }

    const isValid = Boolean(
        name.trim()
        && email.trim()
        && responsibility.trim(),
    );

    return (
        <Dialog
            open={open}
            onClose={closeDialog}
            closeDisabled={saveMutation.isPending}
            title={isEditing ? "Edit contact person" : "Add contact person"}
            description={
                isEditing
                    ? "Update the responsible contact's information."
                    : "Add someone employees can contact for workplace support."
            }
            size="md"
            footer={
                <>
                    <Button
                        variant="secondary"
                        disabled={saveMutation.isPending}
                        onClick={closeDialog}
                    >
                        Cancel
                    </Button>

                    <Button
                        variant="primary"
                        type="submit"
                        form={formId}
                        disabled={saveMutation.isPending || !isValid}
                    >
                        {saveMutation.isPending
                            ? "Saving..."
                            : isEditing
                                ? "Save changes"
                                : "Add contact"}
                    </Button>
                </>
            }
        >
            <form
                id={formId}
                onSubmit={(event) => void handleSubmit(event)}
                className={styles.form}
            >
                <div className={styles.field}>
                    <label htmlFor={`${formId}-name`} className={styles.label}>
                        Full name
                    </label>

                    <Input
                        id={`${formId}-name`}
                        value={name}
                        onChange={(event) => setName(event.target.value)}
                        placeholder="Ada Lovelace"
                        maxLength={150}
                        autoComplete="name"
                        required
                        disabled={saveMutation.isPending}
                    />
                </div>

                <div className={styles.field}>
                    <label htmlFor={`${formId}-email`} className={styles.label}>
                        Work email
                    </label>

                    <Input
                        id={`${formId}-email`}
                        type="email"
                        value={email}
                        onChange={(event) => setEmail(event.target.value)}
                        placeholder="ada.lovelace@company.com"
                        maxLength={254}
                        autoComplete="email"
                        required
                        disabled={saveMutation.isPending}
                    />
                </div>

                <div className={styles.grid}>
                    <div className={styles.field}>
                        <label htmlFor={`${formId}-job-title`} className={styles.label}>
                            Job title
                        </label>

                        <Input
                            id={`${formId}-job-title`}
                            value={jobTitle}
                            onChange={(event) => setJobTitle(event.target.value)}
                            placeholder="HR Manager"
                            maxLength={150}
                            disabled={saveMutation.isPending}
                        />
                    </div>

                    <div className={styles.field}>
                        <label htmlFor={`${formId}-department`} className={styles.label}>
                            Department
                        </label>

                        <Input
                            id={`${formId}-department`}
                            value={department}
                            onChange={(event) => setDepartment(event.target.value)}
                            placeholder="Human Resources"
                            maxLength={150}
                            disabled={saveMutation.isPending}
                        />
                    </div>
                </div>

                <div className={styles.field}>
                    <label htmlFor={`${formId}-responsibility`} className={styles.label}>
                        Responsibility
                    </label>

                    <Input
                        id={`${formId}-responsibility`}
                        value={responsibility}
                        onChange={(event) => setResponsibility(event.target.value)}
                        placeholder="Leave & Absence"
                        maxLength={150}
                        required
                        disabled={saveMutation.isPending}
                    />

                    <p className={styles.hint}>
                        Describe the workplace questions this person handles.
                    </p>
                </div>

                <label className={styles.primaryOption}>
                    <input
                        type="checkbox"
                        checked={isPrimary}
                        onChange={(event) => setIsPrimary(event.target.checked)}
                        disabled={saveMutation.isPending || (isEditing && !contact.is_active)}
                        className={styles.checkbox}
                    />

                    <span className={styles.primaryText}>
                        <span className={styles.primaryTitle}>
                            Primary contact
                        </span>

                        <span className={styles.hint}>
                            Make this person the primary contact for the selected responsibility.
                            Any existing primary contact for that responsibility will be replaced.
                        </span>
                    </span>
                </label>
            </form>
        </Dialog>
    );
}
