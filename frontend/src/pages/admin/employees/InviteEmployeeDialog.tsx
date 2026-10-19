import { useMutation } from "@tanstack/react-query";
import { type SubmitEvent, useState } from "react";
import { toast } from "sonner";

import { Button } from "../../../components/button";
import { Dialog } from "../../../components/dialog/Dialog";
import { Input } from "../../../components/input/Input";
import { Select } from "../../../components/select/Select";
import type { SelectOption } from "../../../components/select/Select.types";
import { inviteEmployee } from "../../../lib/employees";
import type { EmployeeRole } from "../../../types/employee";

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
    const [ email, setEmail ] = useState("");
    const [ role, setRole ] = useState<EmployeeRole>("employee");

    const invitationMutation = useMutation({
        mutationFn: () => inviteEmployee(email.trim().toLowerCase(), role),
    });

    function closeDialog() {
        if (invitationMutation.isPending) {
            return;
        }

        setEmail("");
        setRole("employee");
        invitationMutation.reset();
        onClose();
    }

    async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
        event.preventDefault();

        if (invitationMutation.isPending || !email.trim()) {
            return;
        }

        try {
            const response = await invitationMutation.mutateAsync();

            onInvited();

            if (response.deliveryStatus === "sent") {
                toast.success("Invitation sent successfully.");
            } else {
                toast.warning(
                    "Invitation created, but email delivery needs attention.",
                );
            }

            closeDialog();
        } catch {
            toast.error(
                "Unable to confirm the invitation. Check the employee list before retrying.",
            );
        }
    }

    return (
        <Dialog
            open={open}
            onClose={closeDialog}
            closeDisabled={invitationMutation.isPending}
            title="Invite employee"
            description="Invite an employee to join your NeuroLens workspace."
            size="md"
            footer={
                <>
                    <Button
                        variant="secondary"
                        disabled={invitationMutation.isPending}
                        onClick={closeDialog}
                    >
                        Cancel
                    </Button>

                    <Button
                        variant="primary"
                        type="submit"
                        form="invite-employee-form"
                        disabled={invitationMutation.isPending || !email.trim()}
                    >
                        {invitationMutation.isPending
                            ? "Sending..."
                            : "Send invitation"}
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
                    <label
                        htmlFor="invite-employee-email"
                        className="text-sm font-medium text-fg"
                    >
                        Email address
                    </label>

                    <Input
                        id="invite-employee-email"
                        type="email"
                        value={email}
                        onChange={(event) => setEmail(event.target.value)}
                        placeholder="employee@company.com"
                        autoComplete="email"
                        required
                        disabled={invitationMutation.isPending}
                    />
                </div>

                <div className="flex flex-col gap-2">
                    <label className="text-sm font-medium text-fg">
                        Role
                    </label>

                    <Select
                        options={roleOptions}
                        value={role}
                        onChange={(value) => {
                            if (value !== null) {
                                setRole(value);
                            }
                        }}
                        disabled={invitationMutation.isPending}
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
