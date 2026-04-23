from datetime import datetime
from uuid import uuid4

from app.schemas.campaign import CampaignRecord, PublishChannel, PublishJob


class PublishAdapter:
    async def publish(self, campaign: CampaignRecord, job: PublishJob) -> PublishJob:
        raise NotImplementedError


class MockPublishAdapter(PublishAdapter):
    async def publish(self, campaign: CampaignRecord, job: PublishJob) -> PublishJob:
        external_ids = {
            channel: f"mock-{channel}-{campaign.id[:8]}-{uuid4().hex[:8]}"
            for channel in job.channels
        }
        return job.model_copy(
            update={
                "status": "published",
                "published_at": datetime.now(),
                "updated_at": datetime.now(),
                "provider": "mock",
                "external_ids": external_ids,
                "error_message": None,
            }
        )


def build_publish_adapter() -> PublishAdapter:
    return MockPublishAdapter()

