import json
import os

import requests
from strands import tool

from ctrl_alt_heal.infrastructure.secrets import get_secret


@tool(
    name="search",
    description=(
        "Searches the public web for general information, typically about medications. "
        "Use this to answer questions about what a drug is, its side effects, or common dosages. "
        "Do NOT use this to find user-specific information. "
        "Example Triggers: 'What is Metformin?', 'Tell me about the side effects of Lisinopril.'"
    ),
    inputSchema={
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
)
def search_tool(query: str) -> str:
    """A tool for searching information on the web."""
    api_key = get_secret(os.environ["SERPER_SECRET_NAME"])["api_key"]
    if not api_key:
        return "SERPER_API_KEY not found."

    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}

    try:
        response = requests.request(
            "POST", url, headers=headers, data=payload, timeout=10
        )
        response.raise_for_status()  # Raise an exception for bad status codes
        results = response.json()

        # Process and format results
        output = ""
        if "organic" in results:
            for result in results["organic"][:5]:  # Limit to top 5 results
                output += f"Title: {result.get('title', 'N/A')}\n"
                output += f"Link: {result.get('link', 'N/A')}\n"
                output += f"Snippet: {result.get('snippet', 'N/A')}\n---\n"
        return output or "No results found."
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"
