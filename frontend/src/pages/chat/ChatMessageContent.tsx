import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { visit } from "unist-util-visit";
import type { PhrasingContent, Root } from "mdast";

import type { PolicyCitation } from "../../lib/conversations";
import { getCitedPolicyFileUrl } from "../../lib/policies";
import { chatMessageContentStyles as styles } from "./ChatMessageContent.styles";
import { normalizePolicyCitations } from "../../lib/policy-citations";

interface ChatMessageContentProps {
    content: string;
    citations?: PolicyCitation[] | null;
}

interface PolicyCitationPluginOptions {
    citations: PolicyCitation[];
}

const CITATION_PATTERN = /\[(P\d+)\]/g;

function remarkPolicyCitations({
    citations,
}: PolicyCitationPluginOptions) {
    const citationsByReference = new Map(
        citations.map((citation) => [
            citation.reference,
            citation,
        ]),
    );

    return (tree: Root) => {
        visit(tree, "text", (node, index, parent) => {
            if (
                index === undefined
                || !parent
                || parent.type === "link"
                || parent.type === "linkReference"
                || !CITATION_PATTERN.test(node.value)
            ) {
                CITATION_PATTERN.lastIndex = 0;
                return;
            }

            CITATION_PATTERN.lastIndex = 0;

            const replacements: PhrasingContent[] = [];
            let lastIndex = 0;

            for (const match of node.value.matchAll(CITATION_PATTERN)) {
                const matchIndex = match.index;
                const reference = match[1];
                const citation = citationsByReference.get(reference);

                if (matchIndex > lastIndex) {
                    replacements.push({
                        type: "text",
                        value: node.value.slice(lastIndex, matchIndex),
                    });
                }

                if (citation) {
                    replacements.push({
                        type: "link",
                        url: getCitedPolicyFileUrl(
                            citation.document_id,
                            citation.version_id,
                            citation.page_number,
                        ),
                        children: [
                            {
                                type: "text",
                                value: match[0],
                            },
                        ],
                    });
                } else {
                    replacements.push({
                        type: "text",
                        value: match[0],
                    });
                }

                lastIndex = matchIndex + match[0].length;
            }

            if (lastIndex < node.value.length) {
                replacements.push({
                    type: "text",
                    value: node.value.slice(lastIndex),
                });
            }

            const children = parent.children as PhrasingContent[];

            children.splice(index, 1, ...replacements);

            return index + replacements.length;
        });
    };
}

export function ChatMessageContent({
    content,
    citations = null,
}: ChatMessageContentProps) {

    const normalizedContent = citations?.length
        ? normalizePolicyCitations(content)
        : content;

    const availableCitations = citations ?? [];

    const citationUrls = new Set(
        availableCitations.map((citation) =>
            getCitedPolicyFileUrl(
                citation.document_id,
                citation.version_id,
                citation.page_number,
            ),
        ),
    );

    return (
        <div className={styles.root}>
            <ReactMarkdown
                remarkPlugins={[
                    remarkGfm,
                    [
                        remarkPolicyCitations,
                        { citations: availableCitations },
                    ],
                ]}
                skipHtml
                components={{
                    a: ({ children, href }) => {
                        const isCitation = (
                            href !== undefined
                            && citationUrls.has(href)
                        );

                        return (
                            <a
                                href={href}
                                className={
                                    isCitation
                                        ? styles.citationLink
                                        : styles.link
                                }
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                {children}
                            </a>
                        );
                    },
                    h1: ({ children }) => (
                        <h2 className={styles.heading}>
                            {children}
                        </h2>
                    ),
                    h2: ({ children }) => (
                        <h3 className={styles.heading}>
                            {children}
                        </h3>
                    ),
                    h3: ({ children }) => (
                        <h4 className={styles.subheading}>
                            {children}
                        </h4>
                    ),
                    p: ({ children }) => (
                        <p className={styles.paragraph}>
                            {children}
                        </p>
                    ),
                    ul: ({ children }) => (
                        <ul className={styles.unorderedList}>
                            {children}
                        </ul>
                    ),
                    ol: ({ children }) => (
                        <ol className={styles.orderedList}>
                            {children}
                        </ol>
                    ),
                    li: ({ children }) => (
                        <li className={styles.listItem}>
                            {children}
                        </li>
                    ),
                    blockquote: ({ children }) => (
                        <blockquote className={styles.blockquote}>
                            {children}
                        </blockquote>
                    ),
                    strong: ({ children }) => (
                        <strong className={styles.strong}>
                            {children}
                        </strong>
                    ),
                    code: ({ children, className }) => (
                        <code className={`${styles.code} ${className ?? ""}`}>
                            {children}
                        </code>
                    ),
                }}
            >
                {normalizedContent}
            </ReactMarkdown>
        </div>
    );
}
