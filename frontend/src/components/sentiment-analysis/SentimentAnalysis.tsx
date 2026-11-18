import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ScanHeart } from "lucide-react";

import { Badge, type BadgeVariant } from "../badge/Badge";
import { Button } from "../button";
import { toast } from "../toast";
import {
    analyzeMessageSentiment,
    getConversation,
    type SentimentAnalysisResponse,
    type SentimentLabel,
} from "../../lib/conversations";
import { sentimentAnalysisStyles as styles } from "./SentimentAnalysis.styles";

interface SentimentAnalysisProps {
    conversationId: string;
    messageId: string;
    prediction: SentimentAnalysisResponse | null;
}

const sentimentPresentation: Record<
    SentimentLabel,
    { label: string; variant: BadgeVariant }
> = {
    negative: { label: "Negative", variant: "warning" },
    neutral: { label: "Neutral", variant: "neutral" },
    positive: { label: "Positive", variant: "success" },
};

export function SentimentAnalysis({
    conversationId,
    messageId,
    prediction,
}: SentimentAnalysisProps) {
    const queryClient = useQueryClient();

    const mutation = useMutation({
        mutationFn: () => analyzeMessageSentiment(
            conversationId,
            messageId,
        ),

        onSuccess: (result) => {
            queryClient.setQueryData<
                Awaited<ReturnType<typeof getConversation>>
            >(
                [ "conversation", conversationId ],
                (previous) => {
                    if (!previous) {
                        return previous;
                    }

                    return {
                        ...previous,
                        messages: previous.messages.map((message) =>
                            message.id === messageId
                                ? {
                                    ...message,
                                    sentiment_analysis: result,
                                }
                                : message,
                        ),
                    };
                },
            );
        },

        onError: (error) => {
            toast.error("Unable to analyze sentiment", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
    });

    const result = prediction ?? mutation.data;

    if (!result) {
        return (
            <div className={styles.root}>
                <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    disabled={mutation.isPending}
                    onClick={() => mutation.mutate()}
                >
                    <ScanHeart aria-hidden="true"/>
                    {mutation.isPending
                        ? "Analyzing..."
                        : "Analyze sentiment"}
                </Button>
            </div>
        );
    }

    const presentation = sentimentPresentation[result.label];

    return (
        <section
            className={styles.result}
            aria-label="Sentiment analysis"
        >
            <div className={styles.header}>
                <div className={styles.title}>
                    <ScanHeart
                        className={styles.icon}
                        aria-hidden="true"
                    />
                    <span>Language sentiment</span>
                </div>

                <Badge variant={presentation.variant}>
                    {presentation.label}
                </Badge>
            </div>

            <div className={styles.details}>
                <span className={styles.detailLabel}>
                    Model confidence
                </span>

                <span className={styles.confidenceValue}>
                    {Math.round(result.confidence * 100)}%
                </span>
            </div>

            <p className={styles.disclaimer}>
                This prediction reflects language patterns, not the
                sender's actual emotions or intentions.
            </p>
        </section>
    );

}
