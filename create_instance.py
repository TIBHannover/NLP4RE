#!/usr/bin/env python3
"""
Simple JSON to ORKG Template Instance Creator

This script creates template instances from JSON survey data.
Maps JSON questions to template fields and creates properly typed resources.
"""

import json
import re
import logging
import uuid
import os
from orkg import ORKG
from typing import Dict, Any, List, Optional
from scripts.config import ORKG_HOST, ORKG_USERNAME, ORKG_PASSWORD
from scripts.mappings import (
    predicates_mapping,
    resource_mappings,
    class_mappings,
    integer_literal_keys,
    list_of_other_comments,
    literal_based_resource_mappings,
    url_literal_keys,
)


class NLPRunLogger:
    """Simple file logger focused on domain events (no HTTP noise).
    Writes compact one-line entries without timestamps.
    """

    def __init__(self, run_id: str, base_dir: str):
        self.run_id = run_id
        self.base_dir = base_dir
        self.logs_dir = os.path.join(base_dir, "run_logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        self.log_path = os.path.join(self.logs_dir, f"nlp4re_run_{run_id}.log")
        self._fh = open(self.log_path, "a", encoding="utf-8")
        self.log("run", "start", run_id=run_id)

    def log(self, section: str, message: str, **kwargs):
        parts = [f"[{section}]", message]
        if kwargs:
            kv = " ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
            parts.append(kv)
        line = " ".join(parts)
        self._fh.write(line + "\n")
        self._fh.flush()

    def divider(self, title: Optional[str] = None):
        # Visual divider line in logs to separate sections
        bar = "─" * 60
        if title:
            self.log("sep", f"{bar} {title} {bar}")
        else:
            self.log("sep", bar)

    def close(self):
        try:
            self.log("run", "end", run_id=self.run_id)
        except Exception:
            pass
        try:
            self._fh.close()
        except Exception:
            pass

    def set_instance_id(self, instance_id: str):
        """Rename the log file to include the created instance ID and continue logging."""
        try:
            # Close current file handle before renaming
            try:
                self._fh.flush()
                self._fh.close()
            except Exception:
                pass

            new_log_path = os.path.join(
                self.logs_dir, f"nlp4re_run_{self.run_id}_{instance_id}.log"
            )
            try:
                if os.path.exists(self.log_path):
                    os.rename(self.log_path, new_log_path)
            except Exception:
                # If rename fails for any reason, fallback to new path without renaming
                new_log_path = os.path.join(
                    self.logs_dir, f"nlp4re_run_{self.run_id}_{instance_id}.log"
                )

            self.log_path = new_log_path
            self._fh = open(self.log_path, "a", encoding="utf-8")
            self.log("run", "instance", run_id=self.run_id, instance_id=instance_id)
        except Exception:
            # As a last resort, try to reopen original path to not break logging
            try:
                if self._fh.closed:
                    self._fh = open(self.log_path, "a", encoding="utf-8")
            except Exception:
                pass


class TemplateInstanceCreator:
    """Creates template instances from JSON survey data"""

    def __init__(self):
        """Initialize ORKG connection"""
        # Create domain logger (file only)
        self.run_id = str(uuid.uuid4())[:8]
        self.run_logger = NLPRunLogger(
            self.run_id, os.path.dirname(os.path.abspath(__file__))
        )

        self.orkg = ORKG(
            host=ORKG_HOST,
            creds=(ORKG_USERNAME, ORKG_PASSWORD),
        )
        print("✅ Connected to ORKG")
        self.run_logger.log("connect", "ok", host=ORKG_HOST)

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
            self.run_logger.log("json", "loaded", path=json_file_path)
            return data
        except Exception as e:
            print(f"❌ Error loading JSON file: {e}")
            self.run_logger.log("json", "error", path=json_file_path, error=str(e))
            return {}

    def extract_answer_from_question(
        self, question_data: Dict, resource_mapping_key: str
    ) -> List[Dict[str, str]]:
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
        elif question_data.get("selected_answers"):
            for answer in question_data["selected_answers"]:
                if (
                    answer
                    and answer.strip()
                    and (
                        answer.strip() in ["None"]
                        and "None" in resource_mappings[resource_mapping_key]
                    )
                ):
                    # Do NOT split here. Splitting (comma_separated) is handled later per property.
                    label, desc = self._split_label_and_example(answer.strip())
                    answers.append({"label": label, "description": desc})

        # Extract from options details
        elif question_data.get("options_details"):
            for option in question_data["options_details"]:
                if option.get("is_selected"):
                    # Add label if it exists and is not empty
                    if option.get("label") and option["label"].strip():
                        answer_to_add = option["label"].strip()
                        if answer_to_add and (
                            answer_to_add in ["None"]
                            and "None" in resource_mappings[resource_mapping_key]
                        ):
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
        cleaned = re.sub(r"\(\s*i\.g\.,?[^)]*\)", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\(\s*i\.e\.,?.*", "", cleaned, flags=re.IGNORECASE)

        # Remove everything after we see (e.g.... not even care about the closing bracket only "(", "e", ".", "g"
        # Example: "Open source libraries/software (e.g., python libraries, ..." => "Open source libraries/software"
        cleaned = re.sub(r"\(e\.g\.,.*", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"\(i\.g\.,.*", "", cleaned, flags=re.IGNORECASE).strip()
        # Delete every text in parenthesis
        cleaned = re.sub(r"\(.*?\)", "", cleaned, flags=re.IGNORECASE).strip()

        # # delete the space between "ex1 / ex2" => "ex1/ex2"
        # cleaned = re.sub(r"\s*/\s*", "/", cleaned)

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
        self,
        answer: str,
        resource_mapping_key: str,
        is_last_answer: bool,
        prev_answer: str,
    ) -> Optional[str]:
        """Map an answer to a predefined ORKG resource if available"""
        if resource_mapping_key not in self.resource_mappings:
            return None

        resource_map = self.resource_mappings[resource_mapping_key]

        # Try exact match first
        if answer in resource_map:
            return resource_map[answer]

        if (
            prev_answer.strip().lower() in list_of_other_comments
            and answer.strip().lower() not in list_of_other_comments
        ):
            # Skip creating resources for contextual 'Other/Comments'
            try:
                self.run_logger.log(
                    "unmapped",
                    "other_context_skipped",
                    key=resource_mapping_key,
                    answer=answer,
                )
            except Exception:
                pass
            return self.create_new_resource_for_other(answer, resource_mapping_key)

        # Try case-insensitive match
        for key, value in resource_map.items():
            if key.lower() == answer.lower():
                return value

        # Avoid partial matches to prevent wrong class/resource links

        # Handle "Other/Comments" case - do not create any resource; skip
        answer_lower = answer.lower()
        if "other" in answer_lower or "comment" in answer_lower:
            # Check if this is just "Other/Comments" or has additional text
            if answer.strip().lower() in list_of_other_comments:
                try:
                    self.run_logger.log(
                        "unmapped",
                        "other_value_skipped",
                        key=resource_mapping_key,
                        answer=answer,
                    )
                except Exception:
                    pass
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
                    self.run_logger.log(
                        "resource",
                        "created",
                        label=answer,
                        class_id=class_id,
                        id=resource_id,
                    )
                    return resource_id
        except Exception as e:
            print(f"  ⚠️ Could not create new resource for '{answer}': {e}")

        return None

    def create_literal_or_resource(
        self, answers: List[Dict[str, str]], resource_mapping_key: str
    ) -> List[str]:
        """Create literals or map to resources based on the answers"""
        result_ids = []
        # Do not allow creating new categorical resources when not explicitly mapped
        for answer_obj in answers:
            # answer_obj is dict with keys: label, description
            answer = answer_obj.get("label", "")
            example_desc = answer_obj.get("description")
            # First try to map to existing resource
            index = answers.index(answer_obj)
            is_last_answer = index == len(answers) - 1
            prev_answer = answers[index - 1].get("label", "")
            resource_id = self.map_answer_to_resource(
                answer, resource_mapping_key, is_last_answer, prev_answer
            )
            if resource_id == "resource should not be created":
                self.run_logger.log(
                    "unmapped",
                    "other_value_skipped_resource_should_not_be_created",
                    key=resource_mapping_key,
                    answer=answer,
                )
                continue

            if resource_id:
                result_ids.append(resource_id)
                print(f"  ✅ Mapped '{answer}' to resource: {resource_id}")
                self.run_logger.log(
                    "map",
                    "to_resource",
                    key=resource_mapping_key,
                    answer=answer,
                    object_id=resource_id,
                )
            else:
                # Create literal for text-based answers or unmapped answers
                if resource_mapping_key in literal_based_resource_mappings:
                    # These should be literals
                    try:
                        # Integer literal handling for specific keys
                        if resource_mapping_key in integer_literal_keys:
                            import re as _re

                            match = _re.search(r"[-+]?\\d+", str(answer))
                            if match:
                                int_value = match.group(0)
                                literal_response = self.orkg.literals.add(
                                    label=int_value, datatype="xsd:integer"
                                )
                                self.run_logger.log(
                                    "Integer literal",
                                    "created",
                                    key=resource_mapping_key,
                                    answer=answer,
                                    id=literal_response.content["id"],
                                )
                            else:
                                self.run_logger.log(
                                    "Integer literal",
                                    "fallback_to_text",
                                    key=resource_mapping_key,
                                    answer=answer,
                                )
                                # Fallback to text literal if no integer could be parsed
                                literal_response = self.orkg.literals.add(
                                    label=int(answer), datatype="xsd:integer"
                                )
                        elif resource_mapping_key in url_literal_keys:
                            literal_response = self.orkg.literals.add(
                                label=answer, datatype="xsd:uri"
                            )
                        else:

                            literal_response = self.orkg.literals.add(label=answer)
                        if literal_response.succeeded:
                            literal_id = literal_response.content["id"]
                            result_ids.append(literal_id)
                            print(f"  ✅ Created literal for '{answer}': {literal_id}")
                            # Log literal creation for traceability
                            self.run_logger.log(
                                "literal",
                                "created",
                                key=resource_mapping_key,
                                answer=answer,
                                id=literal_id,
                            )
                    except Exception as e:
                        print(f"  ⚠️ Could not create literal for '{answer}': {e}")
                else:
                    # create a new resource for the answer
                    resource_id = self.create_new_resource_for_other(
                        answer, resource_mapping_key
                    )
                    if resource_id:
                        result_ids.append(resource_id)
                        print(
                            f"  ✅ Created new resource for '{answer}': {resource_id}"
                        )
                        self.run_logger.log(
                            "unmapped",
                            "categorical_created",
                            key=resource_mapping_key,
                            answer=answer,
                            id=resource_id,
                        )
                    else:
                        print(f"  ⚠️ Could not create new resource for '{answer}'")
                        self.run_logger.log(
                            "unmapped",
                            "categorical_skipped",
                            key=resource_mapping_key,
                            answer=answer,
                        )

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
        property_label = property_info.get("label", "")
        self.run_logger.log(
            "property",
            "start",
            predicate_id=property_info.get("predicate_id", ""),
            property_label=property_label,
            key=resource_mapping_key,
            mapping=str(question_mapping),
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
                    all_answers = self.extract_answer_from_question(
                        question, property_info.get("resource_mapping_key")
                    )
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
                    answers = self.extract_answer_from_question(
                        question, property_info.get("resource_mapping_key")
                    )
                    all_answers.extend(answers)
        else:
            question = self.find_question_by_pattern(questions, question_mapping)
            if not question:
                # Respect empty_if_missing: do not create default value
                if property_info.get("empty_if_missing"):
                    self.run_logger.log(
                        "property",
                        "empty_missing",
                        property_label=property_label,
                    )
                    return None
                return None
            all_answers = self.extract_answer_from_question(
                question, property_info.get("resource_mapping_key")
            )

        if not all_answers:
            self.run_logger.log("property", "no_answers", property_label=property_label)
            # Respect empty_if_missing: do not create default value
            if property_info.get("empty_if_missing"):
                return None
            return None
        # Handle comma separation only when explicitly specified
        if property_info.get("comma_separated", True):
            expanded_answers = []
            for answer in all_answers:
                if type(answer) == dict:
                    answer_text = answer.get("label", "")
                    # Keep the dictionary format for create_literal_or_resource
                    if "," in answer_text and len(answer_text.split(",")) > 1:
                        for sub_answer in answer_text.split(","):
                            sub_answer = sub_answer.strip()
                            if sub_answer:
                                expanded_answers.append(
                                    {
                                        "label": sub_answer,
                                        "description": answer.get("description"),
                                    }
                                )
                    else:
                        expanded_answers.append(answer)
                elif type(answer) == str:
                    # Handle string answers
                    if "," in answer and len(answer.split(",")) > 1:
                        for sub_answer in answer.split(","):
                            # TODO: if sub_answer is the last index and it contains "and" remove the "and"
                            index = answer.split(",").index(sub_answer)
                            if (
                                index == len(answer.split(",")) - 1
                                and "and" in sub_answer
                            ):
                                sub_answer = sub_answer.replace("and", "")
                            sub_answer = sub_answer.strip()
                            if sub_answer:
                                expanded_answers.append(
                                    {"label": sub_answer, "description": None}
                                )
                    else:
                        expanded_answers.append({"label": answer, "description": None})
                else:
                    raise ValueError(f"  ❌ Invalid answer type: {type(answer)}")
            all_answers = expanded_answers

        # Create literals or resources
        try:
            extracted = [
                a.get("label", "") if isinstance(a, dict) else str(a)
                for a in all_answers
            ]
            self.run_logger.log(
                "property",
                "answers",
                property_label=property_label,
                key=resource_mapping_key,
                answers=extracted,
            )
        except Exception:
            pass
        result_ids = self.create_literal_or_resource(all_answers, resource_mapping_key)

        # Emit explicit outcome logs so it is clear what happened to the property
        try:
            if result_ids:
                created = [rid for rid in result_ids]
                self.run_logger.log(
                    "property",
                    "values_resolved",
                    property_label=property_label,
                    key=resource_mapping_key,
                    result_ids=created,
                )
            else:
                self.run_logger.log(
                    "property",
                    "skipped",
                    property_label=property_label,
                    key=resource_mapping_key,
                )
        except Exception:
            pass

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
            # Run log: subtemplate header and divider
            self.run_logger.divider(f"SUBTEMPLATE {label}")
            self.run_logger.log(
                "subtemplate",
                "start",
                label=label,
                class_id=class_id,
                subtemplate_id=subtemplate_id,
            )
            # Always create a new subtemplate resource (no ORKG search/reuse)
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
                # Try creating without class specification as fallback
                retry_response = self.orkg.resources.add(label=label, classes=[])
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
                print(f"  ✅ Created subtemplate instance: {instance_id}")

                # Note: Subtemplates already exist in ORKG, no need to materialize
                print(f"    ✅ Using existing subtemplate {subtemplate_id}")

            # Process subtemplate properties
            subtemplate_properties = subtemplate_info.get("subtemplate_properties", {})
            # Visual divider before listing properties in console
            print("    " + "─" * 56)
            for prop_id, prop_info in subtemplate_properties.items():
                # Run log: light divider for each property block
                self.run_logger.divider()
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
                            self.run_logger.log(
                                "property",
                                "10-values_resolved",
                                property_label=prop_info.get("label", ""),
                                key=prop_info.get("resource_mapping_key", ""),
                                result_ids=result_ids,
                            )
                        else:
                            # empty_if_missing means leave property empty (no Not reported fallback)
                            mapping_key = prop_info.get("resource_mapping_key")
                            if mapping_key and prop_info.get("empty_if_missing"):
                                print(
                                    f"    ℹ️ {prop_info.get('label', '')}: missing and configured as empty_if_missing; leaving empty"
                                )
                                continue
                            # if prop_id exists in resource_mappings and the value is "Not reported", then use the mapped resource ID
                            if (
                                mapping_key in self.resource_mappings
                                and "Not reported"
                                in self.resource_mappings[mapping_key]
                            ):
                                not_reported_id = self.resource_mappings[mapping_key][
                                    "Not reported"
                                ]
                                self.orkg.statements.add(
                                    subject_id=instance_id,
                                    predicate_id=prop_id,
                                    object_id=not_reported_id,
                                )
                                print(
                                    f"    ✅ Added property {prop_id} with value {not_reported_id} (Not reported)"
                                )
                            else:
                                # If not reported mapping is missing, create a text literal 'Not reported'
                                try:
                                    lit = self.orkg.literals.add(label="Not reported")
                                    if lit.succeeded:
                                        self.orkg.statements.add(
                                            subject_id=instance_id,
                                            predicate_id=prop_id,
                                            object_id=lit.content["id"],
                                        )
                                        print(
                                            f"    ✅ Added property {prop_id} with text literal 'Not reported'"
                                        )
                                        self.run_logger.log(
                                            "literal",
                                            "created",
                                            key=mapping_key,
                                            answer="Not reported",
                                            id=lit.content["id"],
                                        )
                                    else:
                                        print(f"    ⚠️ No data found - skipping field")
                                except Exception:
                                    print(f"    ⚠️ No data found - skipping field")

            # Run log: subtemplate end and closing divider
            self.run_logger.log(
                "subtemplate",
                "end",
                label=label,
                class_id=class_id,
                subtemplate_id=subtemplate_id,
            )
            self.run_logger.divider()

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

    def extract_paper_title_and_authors(
        self, json_data: Dict[str, Any]
    ) -> tuple[str, str]:
        """Extract paper title and authors from JSON data"""
        questions = json_data.get("questions", [])

        for question in questions:
            if question.get("question_text", "").lower() == "title and authors":
                answer = question.get("answer", "")
                if "\r\r" in answer:
                    title, authors = answer.split("\r\r", 1)
                    return title.strip(), authors.strip()
                elif ",\r" in answer:
                    title, authors = answer.split(",\r", 1)
                    return title.strip(), authors.strip()
                elif "\r" in answer:
                    title, authors = answer.split("\r", 1)
                    return title.strip(), authors.strip()
                else:
                    return answer.strip(), ""

        return "Unknown Paper", ""

    def search_paper_in_orkg(self, paper_title: str) -> Optional[str]:
        """Search for existing paper in ORKG by title"""
        try:
            # Search for papers with similar title
            search_results = self.orkg.resources.get(q=paper_title, exact=False)

            if search_results.succeeded and search_results.content:
                # Look for exact title match first
                for resource in search_results.content:
                    if resource.get("label", "").lower() == paper_title.lower():
                        print(f"  ✅ Found exact match for paper: {resource['id']}")
                        return resource["id"]

                # If no exact match, return the first result
                if search_results.content:
                    first_result = search_results.content[0]
                    print(
                        f"  ⚠️ Found similar paper: {first_result['id']} - {first_result.get('label', '')}"
                    )
                    return first_result["id"]

            print(f"  ⚠️ No existing paper found for: {paper_title}")
            return None

        except Exception as e:
            print(f"  ❌ Error searching for paper: {e}")
            return None

    def link_paper_to_template(self, paper_id: str, template_instance_id: str) -> bool:
        """Create a statement linking paper to template instance"""
        try:
            # Create statement: paper -> contribution -> template_instance
            # The property ID for "contribution" - you may need to adjust this based on your mappings
            contribution_property_id = (
                "P31"  # This should be the correct property ID for "contribution"
            )

            statement_response = self.orkg.statements.add(
                subject_id=paper_id,
                predicate_id=contribution_property_id,
                object_id=template_instance_id,
            )

            if statement_response.succeeded:
                print(
                    f"  ✅ Created statement: {paper_id} -> contribution -> {template_instance_id}"
                )
                return True
            else:
                print(f"  ❌ Failed to create statement: {statement_response.errors}")
                return False

        except Exception as e:
            print(f"  ❌ Error creating statement: {e}")
            return False

    def create_template_instance(self, json_data: Dict[str, Any]) -> Optional[str]:
        """Create a template instance"""

        # Extract paper title and authors from JSON data
        paper_title, paper_authors = self.extract_paper_title_and_authors(json_data)
        print(f"\n📄 Paper: {paper_title}")
        print(f"👥 Authors: {paper_authors}")

        # Search for existing paper in ORKG
        paper_id = self.search_paper_in_orkg(paper_title)

        try:
            # Create the main instance with the target class
            instance_response = self.orkg.resources.add(
                label="NLP4RE ID Card Automated Creation",
                classes=[
                    self.target_class_id,
                    "Contribution",
                ],  # Use the target class directly
            )
            print(instance_response.content)

            if not instance_response.succeeded:
                print(f"❌ Failed to create instance")
                return None

            instance_id = instance_response.content["id"]
            print(f"✅ Created instance: {instance_id}")
            # Update logger file name to include instance ID
            try:
                self.run_logger.set_instance_id(instance_id)
            except Exception:
                pass

            # Instance should be automatically linked to template through the class
            print(
                "✅ Instance created with target class - should be linked to template"
            )

            # ANSI colors for console headings
            ANSI = {
                "reset": "\033[0m",
                "bold": "\033[1m",
                "blue": "\033[34m",
                "magenta": "\033[35m",
                "cyan": "\033[36m",
                "yellow": "\033[33m",
            }

            # Process each predicate in the template
            for predicate_id, predicate_info in self.predicates.items():
                # Run log section divider
                self.run_logger.divider(f"PREDICATE {predicate_id}")
                self.run_logger.log(
                    "section",
                    "predicate",
                    id=predicate_id,
                    label=predicate_info["label"],
                )
                # Console heading with color
                print(
                    f"\n{ANSI['bold']}{ANSI['blue']}🔍 Processing: {predicate_info['label']} ({predicate_id}){ANSI['reset']}"
                )

                if "subtemplate_properties" in predicate_info:
                    # Handle subtemplate fields
                    print(
                        f"{ANSI['magenta']}  📋 Creating subtemplate for {predicate_info['label']}{ANSI['reset']}"
                    )
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
                            # Log link creation
                            try:
                                self.run_logger.log(
                                    "link",
                                    "created",
                                    s=instance_id,
                                    p=predicate_id,
                                    o=subtemplate_id,
                                )
                            except Exception:
                                pass
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
                                link_stmt = self.orkg.statements.add(
                                    subject_id=instance_id,
                                    predicate_id=predicate_id,
                                    object_id=result_id,
                                )

                                if link_stmt.succeeded:
                                    print(
                                        f"  ✅ Linked to instance with predicate {predicate_id}"
                                    )
                                    try:
                                        self.run_logger.log(
                                            "link",
                                            "created",
                                            s=instance_id,
                                            p=predicate_id,
                                            o=result_id,
                                        )
                                    except Exception:
                                        pass
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
                        # empty_if_missing means leave property empty (no Not reported fallback)
                        mapping_key = predicate_info.get("resource_mapping_key")
                        if mapping_key and predicate_info.get("empty_if_missing"):
                            print(
                                f"  ℹ️ {predicate_info.get('label', '')}: missing and configured as empty_if_missing; leaving empty"
                            )
                            continue
                        # if the field has Not reported in resource mappings
                        if (
                            mapping_key in self.resource_mappings
                            and "Not reported" in self.resource_mappings[mapping_key]
                        ):
                            not_reported_id = self.resource_mappings[mapping_key][
                                "Not reported"
                            ]
                            self.orkg.statements.add(
                                subject_id=instance_id,
                                predicate_id=predicate_id,
                                object_id=not_reported_id,
                            )
                            print(
                                f"  ✅ Linked to instance with predicate {predicate_id} and value {not_reported_id} (Not reported)"
                            )
                        else:
                            # If not reported mapping is missing, create a text literal 'Not reported'
                            try:
                                lit = self.orkg.literals.add(label="Not reported")
                                if lit.succeeded:
                                    self.orkg.statements.add(
                                        subject_id=instance_id,
                                        predicate_id=predicate_id,
                                        object_id=lit.content["id"],
                                    )
                                    print(
                                        f"  ✅ Linked to instance with predicate {predicate_id} and text literal 'Not reported'"
                                    )
                                    self.run_logger.log(
                                        "literal",
                                        "created",
                                        key=mapping_key,
                                        answer="Not reported",
                                        id=lit.content["id"],
                                    )
                                else:
                                    print(f"  ⚠️ No data found - skipping field")
                            except Exception:
                                print(f"  ⚠️ No data found - skipping field")

            # Link paper to template instance if paper was found
            if paper_id:
                self.link_paper_to_template(paper_id, instance_id)
            else:
                print(f"  ⚠️ Cannot link paper to template - paper not found in ORKG")

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

    input_json_file = input("Please enter the path to the JSON file: ")

    instance_id = creator.process_json_file(input_json_file)

    if instance_id:
        print(f"\n🎉 SUCCESS! Instance ID: {instance_id}")
        print(f"🌐 View at: https://orkg.org/resource/{instance_id}")
    else:
        print(f"\n❌ Failed to create instance")


if __name__ == "__main__":
    main()
