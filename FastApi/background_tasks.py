"""
Background Tasks for Scholarship Updates
Implements periodic verification of external scholarships
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from database import supabase_admin
from scraper import check_for_updates, ScraperError


# Configuration
CHECK_INTERVAL_HOURS = 24  # How often to check for updates
BATCH_SIZE = 10  # Number of scholarships to check per batch
DELAY_BETWEEN_REQUESTS = 2  # Seconds between requests to avoid rate limiting


class ScholarshipUpdateChecker:
    """
    Background task manager for checking scholarship updates.
    """

    def __init__(self):
        self.is_running = False
        self.last_run = None
        self.results = []

    async def check_single_scholarship(self, scholarship: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks a single scholarship for updates.

        Args:
            scholarship: Scholarship data with id, source_url, checksum

        Returns:
            Result dictionary with update status
        """
        scholarship_id = scholarship.get('id')
        source_url = scholarship.get('source_url')
        stored_checksum = scholarship.get('checksum', '')

        result = {
            "scholarship_id": scholarship_id,
            "checked_at": datetime.utcnow().isoformat(),
            "status": "unknown"
        }

        if not source_url:
            result["status"] = "skipped"
            result["reason"] = "No source URL"
            return result

        try:
            update_result = await check_for_updates(source_url, stored_checksum)

            if update_result.get('error'):
                result["status"] = "error"
                result["error"] = update_result['error']
            elif update_result.get('has_changed'):
                result["status"] = "changed"
                result["new_checksum"] = update_result.get('new_checksum')
            else:
                result["status"] = "unchanged"

            # Update last_checked_at in database
            if supabase_admin:
                update_data = {"last_checked_at": datetime.utcnow().isoformat()}

                if result["status"] == "changed":
                    update_data["needs_review"] = True

                supabase_admin.table('scholarships')\
                    .update(update_data)\
                    .eq('id', scholarship_id)\
                    .execute()

        except ScraperError as e:
            result["status"] = "error"
            result["error"] = e.message
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    async def check_all_external_scholarships(self) -> Dict[str, Any]:
        """
        Checks all external scholarships for updates.

        Returns:
            Summary of the check operation
        """
        if self.is_running:
            return {
                "status": "already_running",
                "message": "Update check is already in progress"
            }

        self.is_running = True
        self.last_run = datetime.utcnow()
        self.results = []

        try:
            if not supabase_admin:
                return {"status": "error", "message": "Database not available"}

            # Get all external scholarships with source URLs
            response = supabase_admin.table('scholarships')\
                .select('id, title, source_url, checksum, last_checked_at')\
                .eq('is_external', True)\
                .not_.is_('source_url', 'null')\
                .execute()

            scholarships = response.data or []

            if not scholarships:
                return {
                    "status": "success",
                    "message": "No external scholarships to check",
                    "total": 0
                }

            # Filter scholarships not checked recently
            scholarships_to_check = []
            cutoff_time = datetime.utcnow() - timedelta(hours=CHECK_INTERVAL_HOURS)

            for scholarship in scholarships:
                last_checked = scholarship.get('last_checked_at')
                if not last_checked:
                    scholarships_to_check.append(scholarship)
                else:
                    try:
                        last_checked_dt = datetime.fromisoformat(
                            last_checked.replace('Z', '+00:00').replace('+00:00', '')
                        )
                        if last_checked_dt < cutoff_time:
                            scholarships_to_check.append(scholarship)
                    except:
                        scholarships_to_check.append(scholarship)

            # Process in batches
            total_checked = 0
            changed_count = 0
            error_count = 0

            for i in range(0, len(scholarships_to_check), BATCH_SIZE):
                batch = scholarships_to_check[i:i + BATCH_SIZE]

                for scholarship in batch:
                    result = await self.check_single_scholarship(scholarship)
                    self.results.append(result)
                    total_checked += 1

                    if result["status"] == "changed":
                        changed_count += 1
                    elif result["status"] == "error":
                        error_count += 1

                    # Delay between requests
                    await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

            return {
                "status": "success",
                "message": f"Checked {total_checked} scholarships",
                "total_checked": total_checked,
                "changed": changed_count,
                "errors": error_count,
                "skipped": len(scholarships) - len(scholarships_to_check),
                "completed_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error during check: {str(e)}"
            }
        finally:
            self.is_running = False

    def get_last_results(self) -> Dict[str, Any]:
        """
        Returns the results from the last update check.
        """
        return {
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "is_running": self.is_running,
            "results_count": len(self.results),
            "results": self.results[-50:]  # Last 50 results
        }


# Global instance
update_checker = ScholarshipUpdateChecker()


async def scheduled_update_check():
    """
    Function to be called by a scheduler (e.g., APScheduler or cron).
    Can be integrated with FastAPI's startup/shutdown events.
    """
    result = await update_checker.check_all_external_scholarships()
    print(f"[{datetime.utcnow().isoformat()}] Scheduled update check completed: {result}")
    return result


def get_checker_status() -> Dict[str, Any]:
    """
    Returns current status of the update checker.
    """
    return {
        "is_running": update_checker.is_running,
        "last_run": update_checker.last_run.isoformat() if update_checker.last_run else None,
        "check_interval_hours": CHECK_INTERVAL_HOURS
    }
