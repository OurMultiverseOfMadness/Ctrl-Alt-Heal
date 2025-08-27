from ics import Calendar, Event
from strands import tool


@tool(
    description="Creates an ICS file for calendar appointments.",
    inputSchema={
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "dtstart": {"type": "string", "format": "date-time"},
            "dtend": {"type": "string", "format": "date-time"},
        },
        "required": ["summary", "dtstart", "dtend"],
    },
)
def calendar_ics_tool(summary: str, dtstart: str, dtend: str) -> str:
    """A tool for creating ICS files."""
    c = Calendar()
    e = Event()
    e.name = summary
    e.begin = dtstart
    e.end = dtend
    c.events.add(e)
    return str(c)
