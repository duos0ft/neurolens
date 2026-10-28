import { useState } from "react";
import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus } from "lucide-react";

import { Button } from "../../../components/button";
import { Filters } from "../../../components/filters/Filters";
import type { FilterDefinition, FilterValues } from "../../../components/filters/Filters.types";
import { PageHeader } from "../../../components/page-header/PageHeader";
import { Table, type TableColumn, type TableRowAction } from "../../../components/table/Table";
import { type ContactPerson, getContactPersons } from "../../../lib/contact-persons";

import { contactPersonsPageStyles as styles } from "./ContactPersonsPage.styles";
import { ContactPersonDialog } from "./ContactPersonDialog";

const PAGE_SIZE = 20;

const contactFilters: FilterDefinition[] = [
    {
        key: "search",
        type: "search",
        placeholder: "Search contacts...",
        debounceMs: 300,
    },
    {
        key: "status",
        type: "segmentedControl",
        label: "Filter contact persons by status",
        options: [
            { label: "Active", value: "active" },
            { label: "All", value: null },
        ],
    },
];

const columns: TableColumn<ContactPerson>[] = [
    {
        key: "name",
        title: "Name",
        render: (contact) => (
            <span className={styles.name}>
                {contact.name}
            </span>
        ),
    },
    {
        key: "email",
        title: "Email",
        render: (contact) => (
            <span className={styles.email}>
                {contact.email}
            </span>
        ),
    },
    {
        key: "responsibility",
        title: "Responsibility",
        render: (contact) => (
            <span className={styles.responsibility}>
                {contact.responsibility}
            </span>
        ),
    },
    {
        key: "department",
        title: "Department",
        render: (contact) => (
            <span className={styles.secondary}>
                {contact.department || "—"}
            </span>
        ),
    },
    {
        key: "primary",
        title: "Primary",
        render: (contact) => (
            contact.is_primary ? (
                <span className={styles.primaryBadge}>
                    Primary
                </span>
            ) : (
                <span className={styles.secondary}>
                    —
                </span>
            )
        ),
    },
    {
        key: "status",
        title: "Status",
        render: (contact) => (
            <span
                className={
                    contact.is_active
                        ? styles.activeBadge
                        : styles.inactiveBadge
                }
            >
                {contact.is_active ? "Active" : "Inactive"}
            </span>
        ),
    },
];

export function Component() {
    const queryClient = useQueryClient();

    const [ dialogOpen, setDialogOpen ] = useState(false);
    const [ editingContact, setEditingContact ] = useState<ContactPerson | null>(null);

    function handleAddContact() {
        setEditingContact(null);
        setDialogOpen(true);
    }

    function handleEditContact(contact: ContactPerson) {
        setEditingContact(contact);
        setDialogOpen(true);
    }

    function handleContactSaved() {
        setPage(1);

        void queryClient.invalidateQueries({
            queryKey: [ "contact-persons" ],
        });
    }

    const [ filters, setFilters ] = useState<FilterValues>({
        search: "",
        status: "active",
    });

    const [ page, setPage ] = useState(1);

    const search = typeof filters.search === "string"
        ? filters.search
        : "";

    const includeInactive = filters.status !== "active";

    const contactsQuery = useQuery({
        queryKey: [
            "contact-persons",
            {
                page,
                pageSize: PAGE_SIZE,
                search,
                includeInactive,
            },
        ],
        queryFn: () => getContactPersons({
            page,
            pageSize: PAGE_SIZE,
            search,
            includeInactive,
        }),
        placeholderData: keepPreviousData,
    });

    const contacts = contactsQuery.data;

    const loading = contactsQuery.isPending;

    const error = contactsQuery.isError
        ? "Unable to load contact persons. Please try again."
        : null;

    function updateFilters(nextFilters: FilterValues) {
        setFilters(nextFilters);
        setPage(1);
    }

    const rowActions: TableRowAction<ContactPerson>[] = [
        {
            label: "Edit contact",
            icon: Pencil,
            onSelect: (contact) => handleEditContact(contact),
        },
    ];

    return (
        <div className={styles.root}>
            <PageHeader
                title="Contact Persons"
                description="Manage the people responsible for workplace questions and employee support."
                actions={
                    <Button
                        variant="primary"
                        onClick={handleAddContact}
                    >
                        <Plus className={styles.actionIcon}/>
                        Add contact
                    </Button>
                }
            />

            <section
                className={styles.directory}
                aria-label="Contact persons directory"
            >
                <div className={styles.toolbar}>
                    <Filters
                        definitions={contactFilters}
                        values={filters}
                        onChange={updateFilters}
                    />
                </div>

                {error ? (
                    <div className={styles.error} role="alert">
                        {error}
                    </div>
                ) : (
                    <Table
                        columns={columns}
                        rowActions={rowActions}
                        rows={contacts?.items ?? []}
                        rowKey={(contact) => contact.id}
                        loading={loading}
                        emptyMessage="No contact persons found. Try adjusting your search or filters."
                        pagination={
                            contacts
                                ? {
                                    page: contacts.page,
                                    pageSize: contacts.page_size,
                                    totalItems: contacts.total_items,
                                    totalPages: contacts.total_pages,
                                    onPageChange: setPage,
                                }
                                : undefined
                        }
                    />
                )}
            </section>

            <ContactPersonDialog
                open={dialogOpen}
                contact={editingContact}
                onClose={() => setDialogOpen(false)}
                onSaved={handleContactSaved}
            />
        </div>
    );
}
