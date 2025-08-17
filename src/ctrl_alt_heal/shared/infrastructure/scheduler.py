from __future__ import annotations

import json
import os

import boto3


class ReminderScheduler:
    """Thin wrapper over EventBridge Scheduler to create recurring reminders."""

    def __init__(self, region_name: str | None = None) -> None:
        self._client = boto3.client("scheduler", region_name=region_name)
        self._group_name = os.getenv("SCHEDULE_GROUP", "default")
        self._target_arn = os.getenv("REMINDER_TARGET_ARN", "")
        self._role_arn = os.getenv("SCHEDULER_ROLE_ARN", "")

    def create_cron_schedules(
        self,
        chat_id: int,
        rx_sk: str,
        times_utc_hhmm: list[str],
        until_iso: str,
    ) -> list[str]:
        """Create one schedule per time of day; return schedule names."""
        names: list[str] = []

        def _sanitize(s: str) -> str:
            # Allow only letters, numbers, hyphen and underscore in schedule names
            import re

            return re.sub(r"[^A-Za-z0-9_-]", "_", s)

        # Parse EndDate if provided
        end_dt = None
        if until_iso:
            try:
                from datetime import datetime

                end_dt = datetime.fromisoformat(until_iso.replace("Z", "+00:00"))
            except Exception:
                end_dt = None
        for t in times_utc_hhmm:
            hh, mm = t.split(":")
            cron = f"{mm} {hh} * * ? *"  # every day at HH:MM UTC
            name = _sanitize(f"rx-{chat_id}-{rx_sk}-{hh}{mm}")
            payload = {
                "chat_id": chat_id,
                "rx_sk": rx_sk,
                "action": "send_reminder",
                "until": until_iso,
            }
            try:
                self._client.create_schedule(
                    Name=name,
                    GroupName=self._group_name,
                    ScheduleExpression=f"cron({cron})",
                    FlexibleTimeWindow={"Mode": "OFF"},
                    Target={
                        "Arn": self._target_arn,
                        "RoleArn": self._role_arn,
                        "Input": json.dumps(payload),
                    },
                    **({"EndDate": end_dt} if end_dt is not None else {}),
                )
            except Exception as e:
                # If schedule already exists, update it idempotently
                msg = str(e)
                if "already exists" in msg or "ConflictException" in msg:
                    try:
                        self._client.update_schedule(
                            Name=name,
                            GroupName=self._group_name,
                            ScheduleExpression=f"cron({cron})",
                            FlexibleTimeWindow={"Mode": "OFF"},
                            Target={
                                "Arn": self._target_arn,
                                "RoleArn": self._role_arn,
                                "Input": json.dumps(payload),
                            },
                            **({"EndDate": end_dt} if end_dt is not None else {}),
                        )
                    except Exception:
                        # Best effort; keep going
                        pass
                else:
                    # Unknown error; re-raise
                    raise
            names.append(name)
        return names

    def delete_schedules(self, names: list[str]) -> None:
        for n in names:
            try:
                self._client.delete_schedule(Name=n, GroupName=self._group_name)
            except Exception:
                # Best effort
                pass

    @staticmethod
    def local_times_to_utc(times_hhmm: list[str], timezone: str) -> list[str]:
        """Convert HH:MM in user's local zone to HH:MM in UTC for daily cron.

        We only need the offset component since dates are daily; beware DST.
        We choose the current offset when converting times; schedules fire at
        equivalent UTC wall-clock times going forward. For full DST correctness,
        we would need Scheduler's timezone support (not available) or adjust
        schedules seasonally.
        """
        try:
            from datetime import datetime
            from zoneinfo import ZoneInfo

            out: list[str] = []
            now = datetime.utcnow()
            for t in times_hhmm:
                hh, mm = t.split(":")
                local = datetime(
                    now.year,
                    now.month,
                    now.day,
                    int(hh),
                    int(mm),
                    tzinfo=ZoneInfo(timezone),
                )
                utc_dt = local.astimezone(ZoneInfo("UTC"))
                out.append(f"{utc_dt.hour:02d}:{utc_dt.minute:02d}")
            return out
        except Exception:
            return times_hhmm

    @staticmethod
    def utc_times_to_local(times_hhmm_utc: list[str], timezone: str) -> list[str]:
        """Convert HH:MM (UTC) to HH:MM in user's local timezone for display."""
        try:
            from datetime import datetime
            from zoneinfo import ZoneInfo

            out: list[str] = []
            now = datetime.utcnow()
            for t in times_hhmm_utc:
                hh, mm = t.split(":")
                utc_dt = datetime(
                    now.year,
                    now.month,
                    now.day,
                    int(hh),
                    int(mm),
                    tzinfo=ZoneInfo("UTC"),
                )
                local = utc_dt.astimezone(ZoneInfo(timezone))
                out.append(f"{local.hour:02d}:{local.minute:02d}")
            return out
        except Exception:
            return times_hhmm_utc
