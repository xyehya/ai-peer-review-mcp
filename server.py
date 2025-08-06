#!/usr/bin/env python

"""
AI Peer Review MCP Server (Python Edition)
Provides peer review feedback using Google Gemini API
"""

import sys
import json
import os
import logging
import re
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'


# --- Logging Setup ---
log_file = os.path.join(os.getcwd(), 'mcp-server.log')
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S.%f%z'
)

def log(message, data=None):
    """Writes a log message to the log file and stderr."""
    log_entry = f"{message}"
    if data:
        log_entry += f"\n{json.dumps(data, indent=2)}"
    logging.info(log_entry)
    # MCP communication is on stdout, so we can use stderr for real-time logs.
    print(f"[MCP LOG] {message}", file=sys.stderr)
    if data:
        print(json.dumps(data, indent=2), file=sys.stderr)


# --- Main Server Loop ---
def main():
    """
    Main loop to read requests from stdin, process them,
    and write responses to stdout.
    """
    log("Starting AI Peer Review MCP Server (Python Edition)")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break # End of input

            request = json.loads(line)
            log("Received request", request)

            response = None
            if request.get("method") == "list_tools":
                response = handle_list_tools(request)
            elif request.get("method") == "call_tool":
                response = handle_call_tool(request)
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32601,
                        "message": "Method not found",
                    },
                }

            write_response(response)

        except json.JSONDecodeError:
            log("Failed to decode JSON from stdin", {"line": line.strip()})
        except Exception as e:
            log("Error in main loop", {"error": str(e)})
            # Attempt to send an error response if possible
            try:
                req_id = json.loads(line).get("id")
                write_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": f"Internal server error: {e}"}
                })
            except:
                pass # Can't send error response if request is malformed
            break

def write_response(response):
    """Serializes a response to JSON and writes it to stdout."""
    if response:
        response_str = json.dumps(response)
        log("Sending response", response)
        print(response_str, file=sys.stdout)
        sys.stdout.flush()

def handle_list_tools(request):
    """Handles the list_tools request."""
    tool_definition = {
        "name": "ai_peer_review",
        "description": "Get peer review feedback from Google Gemini on your response to help improve accuracy and completeness",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_question": {
                    "type": "string",
                    "description": "The original question asked by the user"
                },
                "my_answer": {
                    "type": "string",
                    "description": "Your initial response that needs peer review"
                }
            },
            "required": ["user_question", "my_answer"]
        }
    }
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {"tools": [tool_definition]}
    }

def handle_call_tool(request):
    """Handles the call_tool request."""
    params = request.get("params", {})
    name = params.get("name")
    args = params.get("arguments", {})

    log("Tool call received", {"name": name, "args": args})

    if name == 'ai_peer_review':
        try:
            user_question = args.get('user_question')
            my_answer = args.get('my_answer')

            if not user_question or not my_answer:
                raise ValueError('Both user_question and my_answer are required')

            log('Starting peer review process')

            # Get review from Gemini
            raw_feedback = get_gemini_review(user_question, my_answer)

            # Parse the structured feedback
            structured_feedback = parse_gemini_feedback(raw_feedback)
            log('Parsed feedback', structured_feedback)

            result = {
                "peer_review_feedback": {
                    **structured_feedback,
                    "raw_feedback": raw_feedback,
                    "reviewer": "Google Gemini",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                "usage_note": "Use this feedback to identify areas for improvement in your response. Consider revising your answer to address the points raised in the peer review."
            }

            log('Sending result back to host', {"resultSize": len(json.dumps(result))})

            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }]
                }
            }
        except Exception as e:
            log('Error in ai_peer_review tool', {"error": str(e)})
            error_response = {
                "error": str(e),
                "suggestion": "The peer review service encountered an error. Please check the logs."
            }
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(error_response, indent=2)
                    }],
                    "isError": True
                }
            }

    # Handle unknown tools
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "error": {"code": -32601, "message": f"Unknown tool: {name}"}
    }

# --- Gemini API Interaction ---
def get_gemini_review(user_question, initial_answer):
    """Calls the Google Gemini API for a peer review."""
    if not GEMINI_API_KEY:
        raise ValueError('GEMINI_API_KEY environment variable is required')

    review_prompt = f"""PEER REVIEW REQUEST:

Original Question: "{user_question}"

Initial AI Response: "{initial_answer}"

Please provide constructive peer review feedback in the following format:

ACCURACY ASSESSMENT:
[Evaluate factual correctness and identify any errors]

COMPLETENESS:
[Identify important points or perspectives that are missing]

CLARITY:
[Suggest ways to improve explanation clarity and structure]

IMPROVEMENT SUGGESTIONS:
[Provide specific, actionable suggestions for enhancement]

OVERALL RATING:
[Provide a brief overall assessment: Excellent/Good/Needs Improvement/Poor]

Be constructive, specific, and helpful in your feedback."""

    log('Sending request to Gemini', {
        "question": user_question,
        "answer": initial_answer[:200] + '...',
        "promptLength": len(review_prompt)
    })

    try:
        response = requests.post(
            GEMINI_API_URL,
            headers={
                'Content-Type': 'application/json',
                'X-goog-api-key': GEMINI_API_KEY,
            },
            json={
                "contents": [{
                    "parts": [{
                        "text": review_prompt
                    }]
                }]
            }
        )

        log('Gemini API response status', {"status": response.status_code, "statusText": response.reason})
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        log('Raw Gemini response', data)

        if not data.get('candidates') or not data['candidates'][0].get('content'):
            raise ValueError('Invalid response from Gemini API')

        gemini_review = data['candidates'][0]['content']['parts'][0]['text']
        log('Gemini review text', {"review": gemini_review})
        return gemini_review

    except requests.exceptions.RequestException as e:
        log('Error in get_gemini_review', {"error": str(e)})
        raise ConnectionError(f"Failed to get Gemini review: {e}")


def parse_gemini_feedback(raw_feedback):
    """Parses structured feedback from the Gemini response using regex."""
    sections = {
        'accuracy_assessment': '',
        'completeness': '',
        'clarity': '',
        'improvement_suggestions': '',
        'overall_rating': ''
    }

    patterns = {
        'accuracy_assessment': r'ACCURACY ASSESSMENT:\s*([\s\S]*?)(?=COMPLETENESS:|$)',
        'completeness': r'COMPLETENESS:\s*([\s\S]*?)(?=CLARITY:|$)',
        'clarity': r'CLARITY:\s*([\s\S]*?)(?=IMPROVEMENT SUGGESTIONS:|$)',
        'improvement_suggestions': r'IMPROVEMENT SUGGESTIONS:\s*([\s\S]*?)(?=OVERALL RATING:|$)',
        'overall_rating': r'OVERALL RATING:\s*([\s\S]*?)$'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, raw_feedback, re.IGNORECASE)
        if match:
            sections[key] = match.group(1).strip()

    return sections


if __name__ == "__main__":
    main()
