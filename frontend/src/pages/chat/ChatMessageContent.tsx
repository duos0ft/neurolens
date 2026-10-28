import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { chatMessageContentStyles as styles } from "./ChatMessageContent.styles";

type ChatMessageContentProps = {
    content: string;
};

export function ChatMessageContent({
    content,
}: ChatMessageContentProps) {
    return (
        <div className={styles.root}>
            <ReactMarkdown
                remarkPlugins={[ remarkGfm ]}
                skipHtml
                components={{
                    a: ({ children, href }) => (
                        <a
                            href={href}
                            className={styles.link}
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            {children}
                        </a>
                    ),
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
                {content}
            </ReactMarkdown>
        </div>
    );
}
