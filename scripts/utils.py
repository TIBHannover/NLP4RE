"""
Utility functions for the ORKG Template Creator
"""

import os
import json
from typing import Dict, Any, List


def validate_json_file(file_path: str) -> bool:
    """
    Validate that a JSON file exists and is readable
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{file_path}': {e}")
        return False
    except Exception as e:
        print(f"Error reading '{file_path}': {e}")
        return False


def get_question_stats(json_file_path: str) -> Dict[str, Any]:
    """
    Get statistics about questions in a JSON file
    
    Args:
        json_file_path (str): Path to the JSON file
        
    Returns:
        Dict containing statistics about the questions
    """
    if not validate_json_file(json_file_path):
        return {}
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    questions = data.get("questions", [])
    stats = {
        "total_questions": len(questions),
        "question_types": {},
        "valid_questions": 0,
        "skipped_questions": 0
    }
    
    for question in questions:
        question_type = question.get("type")
        question_text = question.get("question_text")
        
        # Count question types
        if question_type:
            stats["question_types"][question_type] = stats["question_types"].get(question_type, 0) + 1
        
        # Count valid vs skipped questions
        if (question_text and question_type and 
            question_text != "Fc-int01-generateAppearances"):
            stats["valid_questions"] += 1
        else:
            stats["skipped_questions"] += 1
    
    return stats


def print_question_summary(json_file_path: str) -> None:
    """
    Print a summary of questions in the JSON file
    
    Args:
        json_file_path (str): Path to the JSON file
    """
    stats = get_question_stats(json_file_path)
    
    if not stats:
        return
    
    print(f"\nQuestion Summary for '{json_file_path}':")
    print(f"  Total questions: {stats['total_questions']}")
    print(f"  Valid questions: {stats['valid_questions']}")
    print(f"  Skipped questions: {stats['skipped_questions']}")
    
    print("\n  Question types:")
    for q_type, count in stats["question_types"].items():
        print(f"    {q_type}: {count}")


def sanitize_label(label: str) -> str:
    """
    Sanitize a label for use in ORKG
    
    Args:
        label (str): The original label
        
    Returns:
        str: Sanitized label
    """
    if not label:
        return ""
    
    # Remove or replace problematic characters
    sanitized = label.strip()
    
    # Remove excessive whitespace
    sanitized = ' '.join(sanitized.split())
    
    return sanitized


def get_available_json_files(directory: str = "pdf2JSON_Results") -> List[str]:
    """
    Get a list of available JSON files in the specified directory
    
    Args:
        directory (str): Directory to search for JSON files
        
    Returns:
        List[str]: List of JSON file paths
    """
    if not os.path.exists(directory):
        print(f"Directory '{directory}' does not exist.")
        return []
    
    json_files = []
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            if validate_json_file(file_path):
                json_files.append(file_path)
    
    return sorted(json_files)


def print_available_files() -> None:
    """Print all available JSON files for template creation"""
    json_files = get_available_json_files()
    
    if not json_files:
        print("No valid JSON files found in pdf2JSON_Results directory.")
        return
    
    print("Available JSON files for template creation:")
    for i, file_path in enumerate(json_files, 1):
        filename = os.path.basename(file_path)
        print(f"  {i}. {filename}")
        
        # Show basic stats
        stats = get_question_stats(file_path)
        if stats:
            print(f"     -> {stats['valid_questions']} valid questions")
