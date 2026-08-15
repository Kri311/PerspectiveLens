import logging
from typing import List, Dict, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

def detect_level_1_event_blindspots(coverage_matrix: Dict[str, int]) -> List[Dict]:
    """
    Level 1: Did a source group completely ignore this event?
    coverage_matrix: dict mapping source_group to article_count.
    """
    total_articles = sum(coverage_matrix.values())
    if total_articles == 0:
        return []

    blindspots = []
    # If a group has < 5% coverage but another group has > 80% coverage
    max_group = max(coverage_matrix, key=coverage_matrix.get)
    max_coverage_pct = coverage_matrix[max_group] / total_articles
    
    if max_coverage_pct > 0.6:  # Slightly relaxed from 80% for real-world variance
        for group, count in coverage_matrix.items():
            if count / total_articles < 0.05:
                blindspots.append({
                    "blindspot_type": "EVENT",
                    "source_group": group,
                    "score": max_coverage_pct - (count / total_articles),
                    "evidence": {
                        "missing_group": group,
                        "dominant_group": max_group,
                        "dominant_pct": max_coverage_pct
                    }
                })
    return blindspots


def detect_level_2_entity_blindspots(
    group_entities: Dict[str, List[str]]
) -> List[Dict]:
    """
    Level 2: Did a source group ignore a key person/entity that others covered heavily?
    group_entities: dict mapping source_group to list of entities mentioned.
    """
    blindspots = []
    
    # Calculate global entity frequencies
    global_entities = Counter()
    for entities in group_entities.values():
        global_entities.update(entities)
        
    for entity, global_freq in global_entities.items():
        if global_freq < 3: # Ignore rare entities
            continue
            
        # Check if any group completely omitted this highly-discussed entity
        for group, entities in group_entities.items():
            if entity not in entities:
                blindspots.append({
                    "blindspot_type": "ENTITY",
                    "source_group": group,
                    "score": global_freq / 10.0, # Simple heuristic score
                    "evidence": {
                        "omitted_entity": entity,
                        "global_frequency": global_freq
                    }
                })
                
    return blindspots


def detect_level_3_aspect_blindspots(
    group_frames: Dict[str, str]
) -> List[Dict]:
    """
    Level 3: Did a source group focus on a completely different frame/aspect?
    group_frames: dict mapping source_group to its dominant frame (e.g. "Economic")
    """
    blindspots = []
    frames = list(group_frames.values())
    
    if len(set(frames)) > 1:
        # There is a disagreement in framing!
        # E.g., Dravidian = "Policy", Conservative = "Scandal"
        frame_counts = Counter(frames)
        dominant_global_frame = frame_counts.most_common(1)[0][0]
        
        for group, frame in group_frames.items():
            if frame != dominant_global_frame:
                blindspots.append({
                    "blindspot_type": "ASPECT",
                    "source_group": group,
                    "score": 0.8,
                    "evidence": {
                        "group_frame": frame,
                        "dominant_global_frame": dominant_global_frame
                    }
                })
                
    return blindspots
