import json
from datetime import datetime
from uuid import uuid4

from app.config import Settings
from app.schemas.campaign import (
    CampaignRecord,
    CampaignStatus,
    PublishChannel,
    PublishJob,
)
from app.schemas.form import AdGenerationForm
from app.schemas.result import GenerationResult


class CampaignStore:
    def __init__(self, settings: Settings) -> None:
        self.path = settings.campaign_store_path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        form: AdGenerationForm,
        result: GenerationResult,
        uploaded_image_path: str | None = None,
        source_campaign_id: str | None = None,
    ) -> CampaignRecord:
        record = CampaignRecord(
            id=uuid4().hex,
            form=form,
            result=result,
            uploaded_image_path=uploaded_image_path,
            source_campaign_id=source_campaign_id,
        )
        records = self._read_records()
        records.append(record)
        self._write_records(records)
        return record

    def list_recent(self, limit: int = 20) -> list[CampaignRecord]:
        return sorted(
            self._read_records(),
            key=lambda record: record.created_at,
            reverse=True,
        )[:limit]

    def list_due_publish_jobs(
        self,
        due_at: datetime,
        limit: int = 20,
    ) -> list[tuple[CampaignRecord, PublishJob]]:
        due_jobs: list[tuple[CampaignRecord, PublishJob]] = []
        for record in self._read_records():
            for job in record.publish_jobs:
                if job.status == "queued" and job.scheduled_at <= due_at:
                    due_jobs.append((record, job))
        return sorted(due_jobs, key=lambda item: item[1].scheduled_at)[:limit]

    def get(self, campaign_id: str) -> CampaignRecord | None:
        for record in self._read_records():
            if record.id == campaign_id:
                return record
        return None

    def update_status(
        self, campaign_id: str, status: CampaignStatus
    ) -> CampaignRecord | None:
        records = self._read_records()
        updated_record: CampaignRecord | None = None
        for index, record in enumerate(records):
            if record.id == campaign_id:
                updated_record = record.model_copy(
                    update={"status": status, "updated_at": datetime.now()}
                )
                records[index] = updated_record
                break
        if updated_record is not None:
            self._write_records(records)
        return updated_record

    def schedule_publish(
        self,
        campaign_id: str,
        channels: list[PublishChannel],
        scheduled_at: datetime,
        provider: str = "mock",
        recurrence: str = "once",
        sequence_index: int = 1,
        sequence_total: int = 1,
    ) -> CampaignRecord | None:
        records = self._read_records()
        updated_record: CampaignRecord | None = None
        for index, record in enumerate(records):
            if record.id == campaign_id:
                job = PublishJob(
                    id=uuid4().hex,
                    campaign_id=campaign_id,
                    channels=channels,
                    scheduled_at=scheduled_at,
                    provider=provider,
                    recurrence=recurrence,
                    sequence_index=sequence_index,
                    sequence_total=sequence_total,
                )
                updated_record = record.model_copy(
                    update={
                        "status": "scheduled",
                        "updated_at": datetime.now(),
                        "publish_jobs": [*record.publish_jobs, job],
                    }
                )
                records[index] = updated_record
                break
        if updated_record is not None:
            self._write_records(records)
        return updated_record

    def update_publish_job(
        self, campaign_id: str, updated_job: PublishJob
    ) -> CampaignRecord | None:
        records = self._read_records()
        updated_record: CampaignRecord | None = None
        for record_index, record in enumerate(records):
            if record.id != campaign_id:
                continue
            jobs = [
                updated_job if job.id == updated_job.id else job
                for job in record.publish_jobs
            ]
            campaign_status: CampaignStatus = (
                "published" if updated_job.status == "published" else record.status
            )
            updated_record = record.model_copy(
                update={
                    "status": campaign_status,
                    "updated_at": datetime.now(),
                    "publish_jobs": jobs,
                }
            )
            records[record_index] = updated_record
            break
        if updated_record is not None:
            self._write_records(records)
        return updated_record

    def update_result(
        self,
        campaign_id: str,
        result: GenerationResult,
        uploaded_image_path: str | None = None,
    ) -> CampaignRecord | None:
        records = self._read_records()
        updated_record: CampaignRecord | None = None
        for index, record in enumerate(records):
            if record.id != campaign_id:
                continue
            updated_record = record.model_copy(
                update={
                    "result": result,
                    "uploaded_image_path": (
                        uploaded_image_path
                        if uploaded_image_path is not None
                        else record.uploaded_image_path
                    ),
                    "updated_at": datetime.now(),
                }
            )
            records[index] = updated_record
            break
        if updated_record is not None:
            self._write_records(records)
        return updated_record

    def _read_records(self) -> list[CampaignRecord]:
        if not self.path.exists():
            return []
        raw = self.path.read_text(encoding="utf-8").strip()
        if not raw:
            return []
        data = json.loads(raw)
        return [CampaignRecord.model_validate(item) for item in data]

    def _write_records(self, records: list[CampaignRecord]) -> None:
        payload = [
            record.model_dump(mode="json")
            for record in sorted(records, key=lambda item: item.created_at)
        ]
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
