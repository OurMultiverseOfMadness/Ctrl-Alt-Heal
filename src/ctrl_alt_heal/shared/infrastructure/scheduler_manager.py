from __future__ import annotations

import json
import os
from typing import Any

import boto3


class SchedulerManager:
    def __init__(self) -> None:
        self._client = boto3.client(
            "scheduler", region_name=os.environ.get("AWS_REGION", "us-east-1")
        )
        self._group = os.environ.get("SCHEDULE_GROUP", "ctrl-alt-heal-reminders")
        self._target_arn = os.environ.get("REMINDER_TARGET_ARN", "")
        self._role_arn = os.environ.get("SCHEDULER_ROLE_ARN", "")

    def create_one_off_schedule(
        self, *, name: str, iso_utc_time: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        if not self._target_arn or not self._role_arn:
            raise RuntimeError(
                "SchedulerManager not configured: target or role ARN missing"
            )

        response = self._client.create_schedule(
            Name=name,
            GroupName=self._group,
            ScheduleExpression=f"at({iso_utc_time})",
            FlexibleTimeWindow={"Mode": "OFF"},
            Target={
                "Arn": self._target_arn,
                "RoleArn": self._role_arn,
                "Input": json.dumps(payload),
            },
        )
        return response  # type: ignore[no-any-return]
