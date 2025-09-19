#!/usr/bin/env python3
"""
Main script for creating ORKG templates from JSON files
"""

import sys
import os
from .template_creator import TemplateCreator
from .utils import validate_json_file, print_question_summary, print_available_files


def main():
    """Main execution function"""
    print("ORKG Template Creator")
    print("=" * 50)

    # Show available files
    print_available_files()

    # Configuration - you can modify these values
    json_file = "pdf2JSON_Results/Example1-Yang-etal-2011.json"
    template_name = "NLP4RE Paper Analysis Survey"

    print(f"\nUsing configuration:")
    print(f"  JSON file: {json_file}")
    print(f"  Template name: {template_name}")

    # Validate input file
    if not validate_json_file(json_file):
        print("Exiting due to invalid JSON file.")
        sys.exit(1)

    # Show question summary
    print_question_summary(json_file)

    # Create template
    try:
        creator = TemplateCreator()
        template_id = creator.create_template_from_json(json_file, template_name)

        print(f"\nSuccess! Template created with ID: {template_id}")
        print(f"View at: https://incubating.orkg.org/template/{template_id}")

        # Optionally add a sample predicate
        # creator.add_predicate_to_template(template_id, "Additional Notes")

    except Exception as e:
        print(f"Error creating template: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
