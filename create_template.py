#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.template_creator import TemplateCreator


def main():
    json_file = "pdf2JSON_Results/Example1-Yang-etal-2011.json"
    template_name = "NLP4RE Paper Analysis Survey new final with api"

    creator = TemplateCreator()

    print("Choose approach:")
    print("1. SHACL template + instances")
    print("2. Working instances only")

    choice = input("Choice (1-2) [1]: ").strip() or "1"

    try:
        if choice == "1":
            # Create SHACL template
            template_id = creator.create_template_from_json(json_file, template_name)
            print(f"SHACL Template: {template_id}")
            print(f"Template URL: https://incubating.orkg.org/template/{template_id}")

            # Create instances from JSON data
            _create_instances_from_json(
                creator.orkg_conn, json_file, template_name, template_id
            )

        elif choice == "2":
            # Create working instances without template
            _create_working_instances(creator.orkg_conn, template_name)

    except Exception as e:
        print(f"Error: {e}")


def _create_instances_from_json(orkg, json_file, template_name, template_id=None):
    """Create instances from the actual JSON data"""
    import json

    print("Adding JSON data to template...")

    # Load JSON data
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Get the target class - same as used by template
    paper_class = orkg.create_or_find_class(template_name)

    # Create main instance from JSON data
    pdf_name = data.get("pdf_name", "Unknown Paper")
    # Add timestamp to ensure unique instance names
    import datetime

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_name = f"{pdf_name} - {timestamp}"
    instance_id = orkg.create_resource(unique_name, classes=[paper_class])

    # Instance should automatically be linked to template via the target class

    # Process questions and add as properties
    questions = data.get("questions", [])
    added_count = 0

    for question in questions:
        question_text = question.get("question_text")

        # Get answer
        answer = question.get("answer")
        if not answer and question.get("selected_answers"):
            answer = question.get("selected_answers")
        if not answer and question.get("options_details"):
            selected = [
                opt["label"]
                for opt in question.get("options_details", [])
                if opt.get("is_selected")
            ]
            if selected:
                answer = selected

        if not question_text or not answer:
            continue

        if question_text == "Fc-int01-generateAppearances":
            continue

        # Create predicate and add to instance
        try:
            pred_id = orkg.create_or_find_predicate(question_text)

            if isinstance(answer, list):
                answer_text = ", ".join(str(a) for a in answer if a)
            else:
                answer_text = str(answer).strip()

            literal_id = orkg.create_literal(answer_text)
            orkg.add_statement(instance_id, pred_id, literal_id)
            added_count += 1

        except Exception as e:
            print(f"Error adding {question_text}: {e}")

    print(f"Added {added_count} properties to instance: {instance_id}")
    print(f"URL: https://incubating.orkg.org/resource/{instance_id}")


def _create_working_instances(orkg, base_name):
    """Create working instances without template"""
    print("Creating working instances...")

    paper_class = orkg.create_or_find_class(f"{base_name} Papers")

    instance_id = orkg.create_resource("Working Example Paper", classes=[paper_class])

    # Add comprehensive data
    data = {
        "has title": "Understanding NLP in Requirements Engineering",
        "has author": "Research Team",
        "addresses RE task": "Requirements defect detection",
        "uses method": "Natural Language Processing",
        "has result": "85% accuracy improvement",
    }

    for pred_label, value in data.items():
        pred_id = orkg.create_or_find_predicate(pred_label)
        literal_id = orkg.create_literal(value)
        orkg.add_statement(instance_id, pred_id, literal_id)

    print(f"Working instance: {instance_id}")
    print(f"Instance URL: https://incubating.orkg.org/resource/{instance_id}")
    print(f"Class URL: https://incubating.orkg.org/class/{paper_class}")


if __name__ == "__main__":
    main()
