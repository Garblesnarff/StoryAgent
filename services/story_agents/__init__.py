"""
Story Agents Package
Contains the AI agents responsible for different aspects of story generation.
"""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class StoryIdea:
    """Data structure for storing story concepts"""
    title: str
    concept: str
    themes: List[str]
    target_audience: str
    estimated_length: str

@dataclass
class WorldSetting:
    """Data structure for storing world building details"""
    location: str
    time_period: str
    cultural_elements: List[str]
    key_locations: List[str]
    conflicts: List[str]

@dataclass
class PlotHook:
    """Data structure for storing plot development details"""
    inciting_incident: str
    stakes: str
    potential_obstacles: List[str]
    character_roles: List[str]
