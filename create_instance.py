#!/usr/bin/env python3
"""
Simple JSON to ORKG Template Instance Creator

This script creates template instances from JSON survey data.
Maps JSON questions to template fields and creates properly typed resources.
"""

import json
import re
from orkg import ORKG
from typing import Dict, Any, List, Optional
from scripts.config import ORKG_HOST, ORKG_USERNAME, ORKG_PASSWORD
from mappings import predicates_mapping, resource_mappings, class_mappings


class TemplateInstanceCreator:
    """Creates template instances from JSON survey data"""

    def __init__(self):
        """Initialize ORKG connection"""
        self.orkg = ORKG(
            host=ORKG_HOST,
            creds=(ORKG_USERNAME, ORKG_PASSWORD),
        )
        print("✅ Connected to ORKG")

        self.template_id = "R1544125"
        self.target_class_id = "C121001"

        self.resource_mappings = resource_mappings

        self.predicates = predicates_mapping
        self.question_mappings = self.build_question_mappings()

    def build_question_mappings(self) -> Dict[str, str]:
        """Build a mapping from question numbers to predicate IDs"""
        mappings = {}

        def extract_mappings(properties, parent_key=""):
            for prop_id, prop_info in properties.items():
                if isinstance(prop_info, dict) and "question_mapping" in prop_info:
                    question_mapping = prop_info["question_mapping"]
                    if isinstance(question_mapping, list):
                        for q in question_mapping:
                            mappings[q] = prop_id
                    else:
                        mappings[question_mapping] = prop_id

                # Handle nested subtemplate properties
                if (
                    isinstance(prop_info, dict)
                    and "subtemplate_properties" in prop_info
                ):
                    extract_mappings(prop_info["subtemplate_properties"], prop_id)

        extract_mappings(self.predicates)

        return mappings

    def load_json_data(self, json_file_path: str) -> Dict[str, Any]:
        """Load JSON data from file"""
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"✅ Loaded JSON data from {json_file_path}")
            return data
        except Exception as e:
            print(f"❌ Error loading JSON file: {e}")
            return {}

    def extract_answer_from_question(self, question_data: Dict) -> List[Dict[str, str]]:
        """Extract the answer from a question data structure"""
        answers: List[Dict[str, str]] = []

        # Check if question has any meaningful content
        question_text = question_data.get("question_text", "").strip()
        if not question_text:
            return []

        # Extract direct text answers
        if question_data.get("answer"):
            answer = question_data["answer"].strip()
            if answer:
                label, desc = self._split_label_and_example(answer)
                answers.append({"label": label, "description": desc})

        # Extract selected answers from multiple choice
        if question_data.get("selected_answers"):
            for answer in question_data["selected_answers"]:
                if answer and answer.strip() and answer.strip() not in ["None"]:
                    # Do NOT split here. Splitting (comma_separated) is handled later per property.
                    label, desc = self._split_label_and_example(answer.strip())
                    answers.append({"label": label, "description": desc})

        # Extract from options details
        if question_data.get("options_details"):
            for option in question_data["options_details"]:
                if option.get("is_selected"):
                    # Add label if it exists and is not empty
                    if option.get("label") and option["label"].strip():
                        answer_to_add = option["label"].strip()
                        if answer_to_add and answer_to_add not in ["None"]:
                            label, desc = self._split_label_and_example(answer_to_add)
                            answers.append({"label": label, "description": desc})

                    # Add field value if it exists and is meaningful
                    field_value = option.get("field_value", "")
                    if (
                        field_value
                        and field_value.strip()
                        and field_value not in ["Yes", "Off", "", "None"]
                        # field value is not a number string
                        and not field_value.strip().isdigit()
                    ):
                        label, desc = self._split_label_and_example(field_value.strip())
                        answers.append({"label": label, "description": desc})

        # Extract text input value for "Other/Comments" fields
        if question_data.get("text_input_value"):
            text_input = question_data["text_input_value"].strip()
            if text_input and text_input not in ["", "None"]:
                label, desc = self._split_label_and_example(text_input)
                answers.append({"label": label, "description": desc})

        # Clean answers: remove any parenthetical (e.g., ...) fragments and normalize whitespace
        cleaned_answers: List[Dict[str, str]] = []
        for raw in answers:
            if not raw:
                continue
            # raw is dict
            cleaned_label = self._clean_answer_text(raw.get("label", ""))
            cleaned_desc = raw.get("description")
            if cleaned_label:
                candidate = {"label": cleaned_label, "description": cleaned_desc}
                if candidate not in cleaned_answers:
                    cleaned_answers.append(candidate)

        # Filter out empty answers and return
        filtered_answers = [
            ans for ans in cleaned_answers if ans and ans.get("label", "").strip()
        ]
        return filtered_answers

    def _clean_answer_text(self, text: str) -> str:
        """Remove unwanted parenthetical fragments like (e.g., ...) and trim punctuation/whitespace."""
        if not isinstance(text, str):
            return text
        cleaned = text
        # Remove any parenthetical that starts with e.g. (handles (e.g ...), (e.g., ...))
        cleaned = re.sub(r"\(\s*e\.g\.,?[^)]*\)", "", cleaned, flags=re.IGNORECASE)
        # Also remove stray multiple spaces and trailing commas
        cleaned = re.sub(r"\s+", " ", cleaned).strip().strip(",")
        return cleaned

    def _split_label_and_example(self, text: str) -> (str, Optional[str]):
        """Return (label, example_text) where example_text captures (e.g., ...) content if present."""
        if not isinstance(text, str):
            return text, None
        match = re.search(r"\(\s*e\.g\.,?\s*([^)]*)\)", text, flags=re.IGNORECASE)
        example = None
        if match:
            example = match.group(1).strip()
        label = self._clean_answer_text(text)
        if example:
            # Normalize example by removing trailing punctuation
            example = example.strip().strip(",")
        return label, example

    def find_question_by_pattern(
        self, questions: List[Dict], question_id: str
    ) -> Optional[Dict]:
        """Find a question by its ID pattern (e.g., 'I.1', 'II.1', etc.)"""
        for question in questions:
            question_text = question.get("question_text", "")
            if question_text.startswith(f"{question_id}."):
                return question
        return None

    def map_answer_to_resource(
        self, answer: str, resource_mapping_key: str, is_last_answer: bool
    ) -> Optional[str]:
        """Map an answer to a predefined ORKG resource if available"""
        if resource_mapping_key not in self.resource_mappings:
            return None

        resource_map = self.resource_mappings[resource_mapping_key]

        # Try exact match first
        if answer in resource_map:
            return resource_map[answer]

        # Try case-insensitive match
        for key, value in resource_map.items():
            if key.lower() == answer.lower():
                return value

        # Try partial match for common variations
        answer_lower = answer.lower()
        for key, value in resource_map.items():
            key_lower = key.lower()
            if (answer_lower in key_lower or key_lower in answer_lower) and len(
                answer_lower
            ) > 3:
                return value

        # Handle "Other/Comments" case - create new resource
        if "other" in answer_lower or "comment" in answer_lower:
            # Check if this is just "Other/Comments" or has additional text
            if answer.strip().lower() in [
                "other",
                "comments",
                "other/comments",
                "other /comments",
                "other / comments",
                "other (e.g., models, trace links, diagrams, code comments)/comments",
            ]:
                if is_last_answer:
                    # Just "Other/Comments" without specific text - use "Unknown"
                    return self.create_new_resource_for_other(
                        "Unknown", resource_mapping_key
                    )
                else:
                    return "resource should not be created"
            else:
                # There's specific text - use it as the resource label
                return self.create_new_resource_for_other(answer, resource_mapping_key)

            return None

    def create_new_resource_for_other(
        self, answer: str, resource_mapping_key: str
    ) -> Optional[str]:
        """Create a new resource for 'Other/Comments' answers"""
        try:
            # Get the appropriate class for this resource type
            if resource_mapping_key in class_mappings:
                class_id = class_mappings[resource_mapping_key]

                # Create new resource
                resource_response = self.orkg.resources.add(
                    label=answer, classes=[class_id]
                )

                if resource_response.succeeded:
                    resource_id = resource_response.content["id"]
                    print(f"  ✅ Created new resource for '{answer}': {resource_id}")
                    return resource_id
        except Exception as e:
            print(f"  ⚠️ Could not create new resource for '{answer}': {e}")

        return None

    def create_literal_or_resource(
        self, answers: List[Dict[str, str]], resource_mapping_key: str
    ) -> List[str]:
        """Create literals or map to resources based on the answers"""
        result_ids = []

        for answer_obj in answers:
            # answer_obj is dict with keys: label, description
            answer = answer_obj.get("label", "")
            example_desc = answer_obj.get("description")
            # First try to map to existing resource
            index = answers.index(answer_obj)
            is_last_answer = index == len(answers) - 1
            resource_id = self.map_answer_to_resource(
                answer, resource_mapping_key, is_last_answer
            )
            if resource_id == "resource should not be created":
                continue

            if resource_id:
                result_ids.append(resource_id)
                print(f"  ✅ Mapped '{answer}' to resource: {resource_id}")
                # If we captured an example/description, attach it via description predicate if available
                if example_desc:
                    try:
                        literal_resp = self.orkg.literals.add(label=example_desc)
                        if literal_resp.succeeded:
                            # TODO: This doesnt work yet
                            description_predicate = "description"
                            self.orkg.statements.add(
                                subject_id=resource_id,
                                predicate_id=description_predicate,
                                object_id=literal_resp.content["id"],
                            )
                    except Exception:
                        pass
            else:
                # Create literal for text-based answers or unmapped answers
                if resource_mapping_key in [
                    "NLP data item",
                    "NLP data prodcution time",
                    "Natural language",
                    "Number of data sources",
                    "url",
                    "Number of annotators",
                    "Measured agreement",
                    "NLP task output classification label",
                    "NLP task output extracted element",
                    "Baseline comparison details",
                ]:
                    # These should be literals
                    try:
                        literal_response = self.orkg.literals.add(label=answer)
                        if literal_response.succeeded:
                            literal_id = literal_response.content["id"]
                            result_ids.append(literal_id)
                            print(f"  ✅ Created literal for '{answer}': {literal_id}")
                    except Exception as e:
                        print(f"  ⚠️ Could not create literal for '{answer}': {e}")
                else:
                    # For unmapped categorical answers, create new resource
                    if resource_mapping_key in self.resource_mappings:
                        # Create new resource for unmapped answers
                        new_resource_id = self.create_new_resource_for_other(
                            answer, resource_mapping_key
                        )
                        if new_resource_id:
                            result_ids.append(new_resource_id)

        return result_ids

    def process_property(
        self,
        json_data: Dict[str, Any],
        property_info: Dict,
        parent_instance_id: str = None,
    ) -> Optional[str]:
        """Process a single property and create the appropriate ORKG objects"""
        questions = json_data.get("questions", [])

        # Get question mapping - for simple properties, try to infer from description
        question_mapping = property_info.get("question_mapping")
        resource_mapping_key = property_info.get(
            "resource_mapping_key", property_info.get("label", "")
        )

        # If no explicit mapping, try to find question based on description
        if not question_mapping:
            description = property_info.get("description", "").lower()
            # Try to find matching question by description keywords
            for question in questions:
                question_text = question.get("question_text", "").lower()
                if any(
                    keyword in question_text
                    for keyword in description.split()
                    if len(keyword) > 3
                ):
                    all_answers = self.extract_answer_from_question(question)
                    if all_answers:
                        result_ids = self.create_literal_or_resource(
                            all_answers, resource_mapping_key
                        )
                        return result_ids[0] if result_ids else None
            return None

        # Handle multiple question mappings
        if isinstance(question_mapping, list):
            all_answers = []
            for q_id in question_mapping:
                question = self.find_question_by_pattern(questions, q_id)
                if question:
                    answers = self.extract_answer_from_question(question)
                    all_answers.extend(answers)
        else:
            question = self.find_question_by_pattern(questions, question_mapping)
            if not question:
                return None
            all_answers = self.extract_answer_from_question(question)

        if not all_answers:
            return None

        # Handle comma separation only when explicitly specified
        if property_info.get("comma_separated", True):
            expanded_answers = []
            for answer in all_answers:
                if "," in answer and len(answer.split(",")) > 1:
                    for sub_answer in answer.split(","):
                        sub_answer = sub_answer.strip()
                        if sub_answer:
                            expanded_answers.append(sub_answer)
                else:
                    expanded_answers.append(answer)
            all_answers = expanded_answers

        # Create literals or resources
        result_ids = self.create_literal_or_resource(all_answers, resource_mapping_key)

        return result_ids  # Return all IDs to handle multiple answers

    def create_subtemplate_instance_new(
        self, subtemplate_info: Dict, json_data: Dict[str, Any], paper_title: str
    ) -> Optional[str]:
        """Create a subtemplate instance using the new structure"""
        try:
            # Create the subtemplate instance
            subtemplate_id = subtemplate_info.get("subtemplate_id")
            class_id = subtemplate_info.get("class_id")
            label = subtemplate_info.get("label", "Unknown")
            if label == "Evaluation":
                print("*************************")
                print(subtemplate_id, class_id, label)
                print("*************************")

            instance_response = self.orkg.resources.add(
                label=label,
                classes=[class_id] if class_id else [],  # Remove paper title prefix
            )

            if not instance_response.succeeded:
                error_msg = (
                    instance_response.content
                    if hasattr(instance_response, "content")
                    else "Unknown error"
                )
                print(
                    f"  ❌ Failed to create subtemplate instance for {label}: {error_msg}"
                )

                # Classes should already exist in ORKG
                if "invalid_class" in str(error_msg) and class_id:
                    print(f"  ℹ️ Class {class_id} should already exist in ORKG")
                    # Try creating without class specification
                    retry_response = self.orkg.resources.add(
                        label=label, classes=[]  # Remove paper title prefix
                    )
                    if retry_response.succeeded:
                        instance_id = retry_response.content["id"]
                        print(
                            f"  ✅ Created subtemplate instance without class specification: {instance_id}"
                        )
                    else:
                        print(
                            f"  ❌ Failed to create subtemplate instance even without class"
                        )
                        return None
            else:
                instance_id = instance_response.content["id"]
                if label == "Evaluation":
                    print("*************************")
                    print(subtemplate_id, class_id, label)
                    print("*************************")
                print(f"  ✅ Created subtemplate instance: {instance_id}")

            # Note: Subtemplates already exist in ORKG, no need to materialize
            print(f"    ✅ Using existing subtemplate {subtemplate_id}")

            # Process subtemplate properties
            subtemplate_properties = subtemplate_info.get("subtemplate_properties", {})
            for prop_id, prop_info in subtemplate_properties.items():
                if isinstance(prop_info, dict):
                    # Handle nested subtemplates
                    if "subtemplate_properties" in prop_info:
                        nested_instance_id = self.create_subtemplate_instance_new(
                            prop_info, json_data, paper_title
                        )
                        if nested_instance_id:
                            # Link nested instance
                            self.orkg.statements.add(
                                subject_id=instance_id,
                                predicate_id=prop_id,
                                object_id=nested_instance_id,
                            )
                            print(f"    ✅ Linked nested subtemplate {prop_id}")
                    else:
                        # Handle regular property
                        result_ids = self.process_property(
                            json_data, prop_info, instance_id
                        )
                        if result_ids:
                            # Handle multiple results (for comma-separated answers)
                            if not isinstance(result_ids, list):
                                result_ids = [result_ids]

                            for result_id in result_ids:
                                self.orkg.statements.add(
                                    subject_id=instance_id,
                                    predicate_id=prop_id,
                                    object_id=result_id,
                                )
                            print(
                                f"    ✅ Added property {prop_id} with {len(result_ids)} value(s)"
                            )

            return instance_id

        except Exception as e:
            print(f"  ❌ Error creating subtemplate: {e}")
            return None

    def create_literal_for_field(self, field_data: str) -> Optional[str]:
        """Create a literal with just the answer data"""
        if not field_data.strip():
            return None

        try:
            # Create literal with just the clean answer data
            literal_response = self.orkg.literals.add(label=field_data)

            if literal_response.succeeded:
                literal_id = literal_response.content["id"]
                print(f"  ✅ Created literal: {literal_id}")
                return literal_id
            else:
                print(f"  ❌ Failed to create literal")
                return None

        except Exception as e:
            print(f"  ❌ Error creating literal: {e}")
            return None

    def create_template_instance(self, json_data: Dict[str, Any]) -> Optional[str]:
        """Create a template instance"""

        # Get paper title
        paper_title = json_data.get("pdf_name", "").replace(".pdf", "")
        if not paper_title:
            questions = json_data.get("questions", [])
            if questions and "title" in questions[0].get("question_text", "").lower():
                paper_title = questions[0].get("answer", "Unknown Paper")

        print(f"\n📄 Creating instance for: {paper_title}")

        try:
            # Create the main instance with the target class
            instance_response = self.orkg.resources.add(
                label=paper_title,
                classes=[self.target_class_id],  # Use the target class directly
            )
            print(instance_response.content)

            if not instance_response.succeeded:
                print(f"❌ Failed to create instance")
                return None

            instance_id = instance_response.content["id"]
            print(f"✅ Created instance: {instance_id}")

            # Instance should be automatically linked to template through the class
            print(
                "✅ Instance created with target class - should be linked to template"
            )

            # Process each predicate in the template
            for predicate_id, predicate_info in self.predicates.items():
                print(f"\n🔍 Processing: {predicate_info['label']}")

                if "subtemplate_properties" in predicate_info:
                    # Handle subtemplate fields
                    print(f"  📋 Creating subtemplate for {predicate_info['label']}")
                    subtemplate_id = self.create_subtemplate_instance_new(
                        predicate_info, json_data, paper_title
                    )

                    if subtemplate_id:
                        # Link the subtemplate instance to the main instance
                        link_stmt = self.orkg.statements.add(
                            subject_id=instance_id,
                            predicate_id=predicate_id,
                            object_id=subtemplate_id,
                        )

                        if link_stmt.succeeded:
                            print(
                                f"  ✅ Linked subtemplate to instance with predicate {predicate_id}"
                            )
                        else:
                            print(f"  ⚠️ Failed to link subtemplate to instance")
                    else:
                        print(f"  ⚠️ Failed to create subtemplate - skipping field")

                else:
                    # Handle simple fields (without subtemplates)
                    result_ids = self.process_property(
                        json_data, predicate_info, instance_id
                    )

                    if result_ids:
                        # Handle multiple results (for comma-separated answers)
                        if not isinstance(result_ids, list):
                            result_ids = [result_ids]

                        for result_id in result_ids:
                            # Link the result to the instance using the correct predicate
                            try:
                                # if predicate is "RE task" and result_id is not a resource, then create a literal
                                # if predicate_id == "P181002":
                                #     # print debug info
                                #     print("*************************")
                                #     print(f"  🔍 Debug info: {result_id}")
                                #     print("*************************")
                                #     # end the program
                                #     exit()

                                link_stmt = self.orkg.statements.add(
                                    subject_id=instance_id,
                                    predicate_id=predicate_id,
                                    object_id=result_id,
                                )

                                if link_stmt.succeeded:
                                    print(
                                        f"  ✅ Linked to instance with predicate {predicate_id}"
                                    )
                                else:
                                    print(
                                        f"  ⚠️ Failed to link to instance: {link_stmt.content if hasattr(link_stmt, 'content') else 'Unknown error'}"
                                    )
                                    print(
                                        f"  ℹ️ Predicate {predicate_id} should already exist in ORKG"
                                    )
                            except Exception as e:
                                print(f"  ⚠️ Error linking to instance: {e}")
                                print(
                                    f"  ℹ️ Predicate {predicate_id} should already exist in ORKG"
                                )
                    else:
                        print(f"  ⚠️ No data found - skipping field")

            print(f"\n✅ Instance created successfully!")
            print(f"Instance URL: https://orkg.org/resource/{instance_id}")
            return instance_id

        except Exception as e:
            print(f"❌ Error creating instance: {e}")
            return None

    def process_json_file(self, json_file_path: str) -> Optional[str]:
        """Process a JSON file and create template instance"""
        print(f"{'='*60}")
        print(f"PROCESSING: {json_file_path}")
        print(f"{'='*60}")

        json_data = self.load_json_data(json_file_path)
        if not json_data:
            return None

        return self.create_template_instance(json_data)


def main():
    """Main function"""
    creator = TemplateInstanceCreator()

    # Process the JSON file
    json_file = "/Users/amirrezaalasti/Desktop/TIB/nlp4re/pdf2JSON_Results/Example1-Yang-etal-2011.json"

    instance_id = creator.process_json_file(json_file)

    if instance_id:
        print(f"\n🎉 SUCCESS! Instance ID: {instance_id}")
        print(f"🌐 View at: https://orkg.org/resource/{instance_id}")
    else:
        print(f"\n❌ Failed to create instance")


if __name__ == "__main__":
    main()
