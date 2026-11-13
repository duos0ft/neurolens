import { useEffect, useRef, useState } from "react";
import { Copy, MessageCircleQuestion } from "lucide-react";
import { toast } from "sonner";

import { Button } from "../button";
import { Checkbox } from "../checkbox/Checkbox";
import type { ConversationClarifications } from "../../lib/conversations";
import { suggestedClarificationsStyles as styles } from "./SuggestedClarifications.styles";

interface SuggestedClarificationsProps {
    clarifications: ConversationClarifications;
}

interface DraftQuestion {
    text: string;
    selected: boolean;
}

export function SuggestedClarifications({
    clarifications,
}: SuggestedClarificationsProps) {
    const [ questions, setQuestions ] = useState<DraftQuestion[]>(
        () => clarifications.questions.map((question) => ({
            text: question,
            selected: true,
        })),
    );

    const textareaRefs = useRef<(HTMLTextAreaElement | null)[]>([]);

    const [ copying, setCopying ] = useState(false);

    const selectedQuestions = questions
        .filter((question) => question.selected && question.text.trim())
        .map((question) => question.text.trim());

    function updateQuestion(
        index: number,
        changes: Partial<DraftQuestion>,
    ) {
        setQuestions((previous) =>
            previous.map((question, questionIndex) =>
                questionIndex === index
                    ? { ...question, ...changes }
                    : question,
            ),
        );
    }

    function resizeTextarea(element: HTMLTextAreaElement) {
        element.style.height = "auto";
        element.style.height = `${element.scrollHeight}px`;
    }

    useEffect(() => {
        textareaRefs.current.forEach((textarea) => {
            if (textarea) {
                resizeTextarea(textarea);
            }
        });
    }, [ questions ]);

    function getMessage(): string {
        if (selectedQuestions.length === 0) {
            return "";
        }

        return [
            "Hi,",
            "",
            selectedQuestions.length === 1
                ? "I have a question to clarify:"
                : "I have a few questions to clarify:",
            "",
            ...selectedQuestions,
            "",
            "Thanks!",
        ].join("\n");
    }

    async function copyMessage() {
        const message = getMessage();

        if (!message || copying) {
            return;
        }

        setCopying(true);

        try {
            await navigator.clipboard.writeText(message);
            toast.success("Clarification message copied");
        } catch {
            toast.error("Unable to copy message");
        } finally {
            setCopying(false);
        }
    }

    if (questions.length === 0) {
        return null;
    }

    return (
        <section
            className={styles.root}
            aria-label="Suggested clarifications"
        >
            <div className={styles.header}>
                <div className={styles.iconContainer}>
                    <MessageCircleQuestion
                        className={styles.icon}
                        aria-hidden="true"
                    />
                </div>

                <div className={styles.headerContent}>
                    <h3 className={styles.title}>
                        Suggested clarifications
                    </h3>

                    <p className={styles.description}>
                        Select or edit the questions you'd like to ask.
                        Nothing will be sent automatically.
                    </p>
                </div>
            </div>

            <div className={styles.questions}>
                {questions.map((question, index) => (
                    <div
                        key={index}
                        className={styles.questionRow}
                    >
                        <div className={styles.questionCheckbox}>
                            <Checkbox
                                checked={question.selected}
                                onChange={(event) =>
                                    updateQuestion(index, {
                                        selected: event.target.checked,
                                    })
                                }
                                aria-label={`Include question ${index + 1}`}
                            />
                        </div>

                        <textarea
                            ref={(element) => {
                                textareaRefs.current[index] = element;
                            }}
                            className={styles.questionInput}
                            value={question.text}
                            onChange={(event) => {
                                updateQuestion(index, {
                                    text: event.target.value,
                                });
                            }}
                            disabled={!question.selected}
                            rows={1}
                            maxLength={1000}
                            aria-label={`Clarification question ${index + 1}`}
                        />
                    </div>
                ))}
            </div>

            <div className={styles.footer}>
                <span className={styles.selectedCount}>
                    {selectedQuestions.length} of {questions.length}
                    {" "}
                    {questions.length === 1 ? "question" : "questions"}
                    {" "}selected
                </span>

                <Button
                    type="button"
                    variant="secondary"
                    disabled={selectedQuestions.length === 0 || copying}
                    onClick={() => {
                        void copyMessage();
                    }}
                >
                    <Copy/>
                    {copying ? "Copying..." : "Copy message"}
                </Button>
            </div>
        </section>
    );
}
