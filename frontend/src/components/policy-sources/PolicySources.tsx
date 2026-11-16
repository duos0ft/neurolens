import { ExternalLink, FileText } from "lucide-react";

import type { PolicyCitation } from "../../lib/conversations";
import { getCitedPolicyFileUrl } from "../../lib/policies";
import { policySourcesStyles as styles } from "./PolicySources.styles";

interface PolicySourcesProps {
    citations: PolicyCitation[];
}

export function PolicySources({
    citations,
}: PolicySourcesProps) {
    if (citations.length === 0) {
        return null;
    }

    return (
        <section
            className={styles.root}
            aria-label="Policy sources"
        >
            <h3 className={styles.heading}>
                Sources
            </h3>

            <div className={styles.list}>
                {citations.map((citation) => (
                    <a
                        key={`${citation.reference}-${citation.chunk_id}`}
                        href={getCitedPolicyFileUrl(
                            citation.document_id,
                            citation.version_id,
                            citation.page_number,
                        )}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.source}
                    >
                        <div className={styles.icon}>
                            <FileText aria-hidden="true"/>
                        </div>

                        <div className={styles.details}>
                            <span className={styles.title}>
                                {citation.document_title}
                            </span>

                            <span className={styles.metadata}>
                                [{citation.reference}]
                                {" · "}
                                Version {citation.version_number}
                                {citation.page_number !== null && (
                                    <> · Page {citation.page_number}</>
                                )}
                            </span>
                        </div>

                        <ExternalLink
                            className={styles.externalIcon}
                            aria-hidden="true"
                        />
                    </a>
                ))}
            </div>
        </section>
    );
}
