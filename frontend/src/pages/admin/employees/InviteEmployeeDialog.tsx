import { type SubmitEvent, useState } from "react";
import { toast } from "sonner";

import { Button } from "../../../components/button";
import { Dialog } from "../../../components/dialog/Dialog";
import { Select } from "../../../components/select/Select";
import type { SelectOption } from "../../../components/select/Select.types";
import { inviteEmployee } from "../../../lib/employees";
import type { EmployeeRole } from "../../../types/employee";
import { EmailInput } from "../../../components/input/EmailInput";

interface InviteEmployeeDialogProps {
    open: boolean;
    onClose: () => void;
    onInvited: () => void;
}

const roleOptions: SelectOption<EmployeeRole>[] = [
    { label: "Employee", value: "employee" },
    { label: "Admin", value: "admin" },
];

export function InviteEmployeeDialog({
    open,
    onClose,
    onInvited,
}: InviteEmployeeDialogProps) {
    const [ emails, setEmails ] = useState<string[]>([]);
    const [ role, setRole ] = useState<EmployeeRole>("employee");
    const [ submitting, setSubmitting ] = useState(false);

    function closeDialog() {
        if (submitting) return;

        setEmails([]);
        setRole("employee");
        onClose();
    }

    async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
        event.preventDefault();

        if (submitting || emails.length === 0) return;

        setSubmitting(true);

        const remaining: string[] = [];
        const messages: string[] = [];
        let delivered = 0;
        let created = 0;

        try {
            for (const email of emails) {
                try {
                    const response = await inviteEmployee(email, role);

                    created++;

                    if (response.deliveryStatus === "sent") {
                        delivered++;
                    } else {
                        messages.push(
                            `${email}: Invitation created, delivery status is ${response.deliveryStatus}.`,
                        );
                    }
                } catch {
                    remaining.push(email);
                    messages.push(
                        `${email}: Unable to confirm whether the invitation was created.`,
                    );
                }
            }

            if (created > 0) {
                onInvited();
            }

            if (delivered > 0) {
                toast.success(
                    `${delivered} invitation${delivered === 1 ? "" : "s"} sent successfully.`,
                );
            }

            if (messages.length > 0) {
                toast.warning(
                    `${messages.length} invitation${messages.length === 1 ? "" : "s"} need attention. Check Invitations for details.`,
                );
            }

        } finally {
            setSubmitting(false);
            closeDialogAfterSuccess();
        }
    }

    function closeDialogAfterSuccess() {
        setEmails([]);
        setRole("employee");
        onClose();
    }

    return (
        <Dialog
            open={open}
            onClose={closeDialog}
            closeDisabled={submitting}
            title="Invite people"
            description="Invite people to join your NeuroLens workspace."
            size="md"
            footer={
                <>
                    <Button
                        variant="secondary"
                        disabled={submitting}
                        onClick={closeDialog}
                    >
                        Cancel
                    </Button>

                    <Button
                        variant="primary"
                        type="submit"
                        form="invite-employee-form"
                        disabled={submitting || emails.length === 0}
                    >
                        {submitting
                            ? "Sending..."
                            : `Send ${emails.length} invitation${emails.length === 1 ? "" : "s"}`}
                    </Button>
                </>
            }
        >
            <form
                id="invite-employee-form"
                onSubmit={(event) => void handleSubmit(event)}
                className="flex flex-col gap-5"
            >
                <div className="flex flex-col gap-2">
                    <label className="text-sm font-medium text-fg">
                        Email addresses
                    </label>

                    <EmailInput
                        values={emails}
                        onChange={(values: string[]) => {
                            setEmails(values);
                        }}
                        disabled={submitting}
                    />

                    <p className="text-xs text-fg-muted">
                        Press Enter or comma to add an email address.
                    </p>
                </div>

                <div className="flex flex-col gap-2">
                    <label className="text-sm font-medium text-fg">
                        Role
                    </label>

                    <Select
                        options={roleOptions}
                        value={role}
                        onChange={(value) => {
                            if (value !== null) setRole(value);
                        }}
                        disabled={submitting}
                        placeholder="Select role"
                    />

                    <p className="text-xs text-fg-muted">
                        {role === "admin"
                            ? "Administrators can manage employees and invitations."
                            : "Employees can use NeuroLens without administrator access."}
                    </p>
                </div>
            </form>
        </Dialog>
    );
}
