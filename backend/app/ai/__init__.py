"""The `ai` domain: owns AI session events and assembles admission reports.

It consumes kaoyan (data), kaogong, and llm (provider). It owns only its own
session-event state; it never becomes a second owner of admission data.
"""
