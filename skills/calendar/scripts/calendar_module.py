#!/usr/bin/env python3
"""
Google Calendar Module for ChatGPT Skills
Manage calendar events, reminders, and bookings

Features:
- List upcoming events
- Create/update/delete events
- Set reminders
- Check availability
- Quick event creation with natural language

Usage:
    python3 calendar_module.py list
    python3 calendar_module.py create "Meeting with John" --start "2026-01-15 10:00" --duration 60
    python3 calendar_module.py remind "Call mom" --time "2026-01-11 18:00"
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from pathlib import Path

# Google API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

# OAuth scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Paths
CREDENTIALS_DIR = os.path.expanduser("~/.claude/credentials")
TOKEN_PATH = os.path.join(CREDENTIALS_DIR, "google_calendar_token.json")  # Changed from pickle to JSON
CREDENTIALS_PATH = os.path.join(CREDENTIALS_DIR, "google_credentials.json")

# Default timezone - uses system timezone
def get_default_timezone() -> str:
    """Get system timezone or fallback to UTC"""
    try:
        import subprocess
        result = subprocess.run(['date', '+%Z'], capture_output=True, text=True)
        tz = result.stdout.strip()
        # Map common abbreviations to IANA timezone
        tz_map = {
            'CST': 'Asia/Shanghai',
            'PST': 'America/Los_Angeles',
            'EST': 'America/New_York',
            'UTC': 'UTC',
            'GMT': 'UTC',
        }
        return tz_map.get(tz, 'UTC')
    except Exception:
        return 'UTC'

DEFAULT_TIMEZONE = get_default_timezone()


class CalendarClient:
    """Google Calendar client for ChatGPT Skills"""

    def __init__(self):
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        if not GOOGLE_API_AVAILABLE:
            print("Error: Google API libraries not installed.")
            print("Run: pip3 install --break-system-packages google-auth-oauthlib google-api-python-client")
            return

        os.makedirs(CREDENTIALS_DIR, exist_ok=True)
        creds = None

        # Load existing token (JSON format)
        if os.path.exists(TOKEN_PATH):
            try:
                creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Warning: Invalid token file, will re-authenticate: {e}")
                creds = None

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None

            if not creds:
                if not os.path.exists(CREDENTIALS_PATH):
                    print(f"\n⚠️  Google credentials not found!")
                    print(f"\nTo set up Google Calendar integration:")
                    print(f"1. Go to https://console.cloud.google.com/")
                    print(f"2. Create a new project or select existing")
                    print(f"3. Enable 'Google Calendar API'")
                    print(f"4. Create OAuth 2.0 credentials (Desktop app)")
                    print(f"5. Download the JSON and save as:")
                    print(f"   {CREDENTIALS_PATH}")
                    print(f"\nThen run this script again to authenticate.")
                    return

                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save token (JSON format - more secure than pickle)
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())

        self.service = build('calendar', 'v3', credentials=creds)

    def _ensure_service(self):
        """Ensure service is available"""
        if not self.service:
            return {"error": "Not authenticated. Please set up Google credentials."}
        return None

    def list_events(self, max_results: int = 10, time_min: str = None,
                    time_max: str = None, calendar_id: str = 'primary') -> Dict:
        """List upcoming calendar events"""
        error = self._ensure_service()
        if error:
            return error

        try:
            if not time_min:
                time_min = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            return {
                "success": True,
                "count": len(events),
                "events": [{
                    "id": e.get('id'),
                    "summary": e.get('summary', 'No title'),
                    "start": e.get('start', {}).get('dateTime', e.get('start', {}).get('date')),
                    "end": e.get('end', {}).get('dateTime', e.get('end', {}).get('date')),
                    "location": e.get('location', ''),
                    "description": e.get('description', ''),
                    "attendees": [a.get('email') for a in e.get('attendees', [])],
                    "link": e.get('htmlLink', '')
                } for e in events]
            }

        except HttpError as e:
            return {"error": f"API error: {e}"}
        except Exception as e:
            return {"error": str(e)}

    def create_event(self, summary: str, start: str, end: str = None,
                     duration: int = 60, description: str = None,
                     location: str = None, attendees: List[str] = None,
                     reminders: List[int] = None, calendar_id: str = 'primary') -> Dict:
        """
        Create a new calendar event

        Args:
            summary: Event title
            start: Start time (ISO format or "YYYY-MM-DD HH:MM")
            end: End time (optional, uses duration if not provided)
            duration: Duration in minutes (default 60)
            description: Event description
            location: Event location
            attendees: List of email addresses
            reminders: List of reminder minutes before event [10, 30]
        """
        error = self._ensure_service()
        if error:
            return error

        try:
            # Parse start time
            start_dt = self._parse_datetime(start)
            if not start_dt:
                return {"error": f"Invalid start time format: {start}"}

            # Calculate end time
            if end:
                end_dt = self._parse_datetime(end)
            else:
                end_dt = start_dt + timedelta(minutes=duration)

            # Build event body
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': DEFAULT_TIMEZONE,
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': DEFAULT_TIMEZONE,
                },
            }

            if description:
                event['description'] = description

            if location:
                event['location'] = location

            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]

            # Set reminders
            if reminders:
                event['reminders'] = {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': m} for m in reminders
                    ]
                }

            # Create event
            created = self.service.events().insert(
                calendarId=calendar_id,
                body=event,
                sendUpdates='all' if attendees else 'none'
            ).execute()

            return {
                "success": True,
                "message": f"Event '{summary}' created",
                "event": {
                    "id": created.get('id'),
                    "summary": created.get('summary'),
                    "start": created.get('start', {}).get('dateTime'),
                    "end": created.get('end', {}).get('dateTime'),
                    "link": created.get('htmlLink')
                }
            }

        except HttpError as e:
            return {"error": f"API error: {e}"}
        except Exception as e:
            return {"error": str(e)}

    def create_reminder(self, title: str, time: str,
                        remind_before: List[int] = None) -> Dict:
        """
        Create a reminder (short event with notifications)

        Args:
            title: Reminder title
            time: When to remind (ISO format or "YYYY-MM-DD HH:MM")
            remind_before: Minutes before to remind [0, 10, 30]
        """
        if remind_before is None:
            remind_before = [0, 10]  # Default: at time and 10 min before

        return self.create_event(
            summary=f"⏰ {title}",
            start=time,
            duration=15,  # Short duration for reminders
            reminders=remind_before
        )

    def quick_add(self, text: str, calendar_id: str = 'primary') -> Dict:
        """
        Quick add event using natural language

        Examples:
            "Lunch with John tomorrow at noon"
            "Meeting at 3pm on Friday"
            "Dentist appointment Jan 15 10am"
        """
        error = self._ensure_service()
        if error:
            return error

        try:
            created = self.service.events().quickAdd(
                calendarId=calendar_id,
                text=text
            ).execute()

            return {
                "success": True,
                "message": f"Event created from: '{text}'",
                "event": {
                    "id": created.get('id'),
                    "summary": created.get('summary'),
                    "start": created.get('start', {}).get('dateTime', created.get('start', {}).get('date')),
                    "end": created.get('end', {}).get('dateTime', created.get('end', {}).get('date')),
                    "link": created.get('htmlLink')
                }
            }

        except HttpError as e:
            return {"error": f"API error: {e}"}
        except Exception as e:
            return {"error": str(e)}

    def update_event(self, event_id: str, summary: str = None,
                     start: str = None, end: str = None,
                     description: str = None, location: str = None,
                     calendar_id: str = 'primary') -> Dict:
        """Update an existing event"""
        error = self._ensure_service()
        if error:
            return error

        try:
            # Get existing event
            event = self.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            # Update fields
            if summary:
                event['summary'] = summary
            if description:
                event['description'] = description
            if location:
                event['location'] = location
            if start:
                start_dt = self._parse_datetime(start)
                event['start'] = {'dateTime': start_dt.isoformat(), 'timeZone': DEFAULT_TIMEZONE}
            if end:
                end_dt = self._parse_datetime(end)
                event['end'] = {'dateTime': end_dt.isoformat(), 'timeZone': DEFAULT_TIMEZONE}

            updated = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()

            return {
                "success": True,
                "message": "Event updated",
                "event": {
                    "id": updated.get('id'),
                    "summary": updated.get('summary'),
                    "start": updated.get('start', {}).get('dateTime'),
                    "link": updated.get('htmlLink')
                }
            }

        except HttpError as e:
            return {"error": f"API error: {e}"}
        except Exception as e:
            return {"error": str(e)}

    def delete_event(self, event_id: str, calendar_id: str = 'primary') -> Dict:
        """Delete an event"""
        error = self._ensure_service()
        if error:
            return error

        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            return {
                "success": True,
                "message": f"Event {event_id} deleted"
            }

        except HttpError as e:
            return {"error": f"API error: {e}"}
        except Exception as e:
            return {"error": str(e)}

    def check_availability(self, start: str, end: str,
                          calendar_id: str = 'primary') -> Dict:
        """Check if a time slot is available"""
        error = self._ensure_service()
        if error:
            return error

        try:
            start_dt = self._parse_datetime(start)
            end_dt = self._parse_datetime(end)

            events = self.list_events(
                time_min=start_dt.isoformat() + 'Z',
                time_max=end_dt.isoformat() + 'Z',
                calendar_id=calendar_id
            )

            if "error" in events:
                return events

            is_available = events.get("count", 0) == 0

            return {
                "success": True,
                "available": is_available,
                "start": start,
                "end": end,
                "conflicts": events.get("events", []) if not is_available else []
            }

        except Exception as e:
            return {"error": str(e)}

    def get_today_events(self) -> Dict:
        """Get all events for today"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)

        return self.list_events(
            time_min=today.isoformat() + 'Z',
            time_max=tomorrow.isoformat() + 'Z',
            max_results=50
        )

    def get_week_events(self) -> Dict:
        """Get all events for this week"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = today + timedelta(days=7)

        return self.list_events(
            time_min=today.isoformat() + 'Z',
            time_max=week_end.isoformat() + 'Z',
            max_results=100
        )

    def list_calendars(self) -> Dict:
        """List all available calendars"""
        error = self._ensure_service()
        if error:
            return error

        try:
            calendars = self.service.calendarList().list().execute()

            return {
                "success": True,
                "calendars": [{
                    "id": c.get('id'),
                    "summary": c.get('summary'),
                    "primary": c.get('primary', False),
                    "access_role": c.get('accessRole')
                } for c in calendars.get('items', [])]
            }

        except HttpError as e:
            return {"error": f"API error: {e}"}
        except Exception as e:
            return {"error": str(e)}

    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Parse datetime from various formats"""
        formats = [
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d",
            "%m/%d/%Y %H:%M",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue

        # Try ISO format
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass

        return None


def main():
    parser = argparse.ArgumentParser(description="Google Calendar for ChatGPT Skills")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # List command
    list_parser = subparsers.add_parser('list', help='List upcoming events')
    list_parser.add_argument('-n', '--max', type=int, default=10, help='Max events')
    list_parser.add_argument('--today', action='store_true', help='Today only')
    list_parser.add_argument('--week', action='store_true', help='This week')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create event')
    create_parser.add_argument('title', help='Event title')
    create_parser.add_argument('--start', required=True, help='Start time')
    create_parser.add_argument('--end', help='End time')
    create_parser.add_argument('--duration', type=int, default=60, help='Duration (min)')
    create_parser.add_argument('--location', help='Location')
    create_parser.add_argument('--description', help='Description')
    create_parser.add_argument('--attendees', nargs='+', help='Attendee emails')

    # Quick add
    quick_parser = subparsers.add_parser('quick', help='Quick add with natural language')
    quick_parser.add_argument('text', help='Event description')

    # Reminder
    remind_parser = subparsers.add_parser('remind', help='Create reminder')
    remind_parser.add_argument('title', help='Reminder title')
    remind_parser.add_argument('--time', required=True, help='Reminder time')

    # Delete
    delete_parser = subparsers.add_parser('delete', help='Delete event')
    delete_parser.add_argument('event_id', help='Event ID')

    # Calendars
    subparsers.add_parser('calendars', help='List calendars')

    # Setup
    subparsers.add_parser('setup', help='Setup Google Calendar')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    client = CalendarClient()

    if args.command == 'setup':
        if client.service:
            print("✅ Google Calendar is already set up!")
            calendars = client.list_calendars()
            if "calendars" in calendars:
                print("\nAvailable calendars:")
                for cal in calendars["calendars"]:
                    primary = " (primary)" if cal.get("primary") else ""
                    print(f"  - {cal['summary']}{primary}")
        return

    if args.command == 'list':
        if args.today:
            result = client.get_today_events()
        elif args.week:
            result = client.get_week_events()
        else:
            result = client.list_events(max_results=args.max)

    elif args.command == 'create':
        result = client.create_event(
            summary=args.title,
            start=args.start,
            end=args.end,
            duration=args.duration,
            location=args.location,
            description=args.description,
            attendees=args.attendees
        )

    elif args.command == 'quick':
        result = client.quick_add(args.text)

    elif args.command == 'remind':
        result = client.create_reminder(args.title, args.time)

    elif args.command == 'delete':
        result = client.delete_event(args.event_id)

    elif args.command == 'calendars':
        result = client.list_calendars()

    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
