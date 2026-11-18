from enum import StrEnum

from pydantic import BaseModel


class ProvisioningStatus(StrEnum):
    COMPLETED = "completed"
    NOT_CLAIMED = "not_claimed"
    FAILED = "failed"
    RECONCILIATION_REQUIRED = "reconciliation_required"


class ProvisioningResult(BaseModel):
    status: ProvisioningStatus
    error_code: str | None = None
