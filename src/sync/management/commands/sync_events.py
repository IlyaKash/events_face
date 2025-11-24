from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
import requests
from src.sync.models import SyncResult, SyncSettings
from src.events.models import Event, Venue, EventStatus

class Command(BaseCommand):
    help="Syncronize events with event-provider API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action='store_true',
            help="Perform full synchronization of all events"
        )
        parser.add_argument(
            "--date",
            type=str,
            help="Synchronize events changed from specific date (YYYY-MM-DD)",
        )
    
    def handle(self, *args, **options):
        sync_result=SyncResult.objects.create(
            sync_type="full" if options["all"] else "incremental",
            added_count=0,
            updated_count=0,
        )

        try:
            self.stdout.write("Starting events synchronization...")

            last_sync_date=self.get_last_sync_date(options)

            added, updated=self.sync_events(last_sync_date, options['all'])

            sync_result.finished_at=timezone.now()
            sync_result.added_count=added
            sync_result.updated_count=updated
            sync_result.is_success=True
            sync_result.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully synchronized events: {added} added, {updated} updated" 
                )
            )

        except Exception as e:
            sync_result.finished_at=timezone.now()
            sync_result.error_message=str(e)
            sync_result.save()
            self.stdout.write(self.style.ERROR(f"Synchronization failed: {str(e)}"))
    
    def get_last_sync_date(self, options):
        """Получаем дату последней синхронизации"""

        if options["all"]:
            return None
        
        if options['date']:
            try:
                return datetime.strptime(options['date'], "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        
        last_event=Event.objects.order_by("-updated_at").first()
        if last_event:
            return last_event.updated_at.date()
        
        last_sync_setting = SyncSettings.objects.filter(key="last_successful_sync").first()
        if last_sync_setting and last_sync_setting.value:
            try:
                return datetime.strptime(last_sync_setting.value, "%Y-%m-%d").date()
            except ValueError:
                pass

        return None
    
    def sync_events(self, last_sync_date=None, full_sync=False):
        """Синхронизация мероприятий с event-provider"""

        base_url="https://events.k3scluster.tech/api/events/"
        added_count=0
        updated_count=0

        params={}
        if not full_sync and last_sync_date:
            params["changed_at"] = last_sync_date.strftime("%Y-%m-%d")

        headers = {
            'accept': 'application/json',
            'User-Agent': 'Events-Face-Sync/1.0',
            'authorization': 'Basic dXNlcjp1c2Vy',
            'X-CSRFTOKEN': 'Qy5MPkhFpPVFvwZt4NlwB6jail7aakjSqnicG7GmOw5DXw70q4nzJrZoLam7H6fu'
        }

        self.stdout.write(f"Fetching events from {base_url} with params: {params}")

        try:
            response=requests.get(base_url, params=params, headers=headers, timeout=30)
            self.stdout.write(f"Response status: {response.status_code}")
            response.raise_for_status()
            events_data=response.json()

            if isinstance(events_data, dict) and "results" in events_data:
                events_list=events_data['results']
            else:
                events_list=events_data
            
            self.stdout.write(f"Received {len(events_list)} events")

            for event_data in events_list:
                try:
                    event, created=self.create_or_update_event(event_data)
                    if created:
                        added_count+=1
                    else:
                        updated_count+=1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Failed to process event {event_data.get('id')}: {str(e)}")
                    )
            
            if added_count>0 or updated_count>0:
                self.save_sync_settings()
            
            return added_count, updated_count
        except requests.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def create_or_update_event(self, event_data):
        """Создает или обновляет мероприятие"""

        venue=None
        if event_data.get("venue"):
            venue, _=Venue.objects.get_or_create(
                id=event_data['venue']['id'],
                defaults={'name': event_data['venue']['name']}
            )
        
        status=EventStatus.OPEN if event_data.get('status') == "open" else EventStatus.CLOSED

        event, created=Event.objects.update_or_create(
            id=event_data['id'],
            defaults={
                "name" : event_data["name"],
                "event_date": event_data["event_date"],
                "status": status,
                "venue": venue,
            }
        )
        return event, created
    
    def save_sync_settings(self):
        setting, _ =SyncSettings.objects.get_or_create(key="last_successful_sync")
        setting.value=timezone.now().date().isoformat()
        setting.description="Date of last successful synchronization"
        setting.save()