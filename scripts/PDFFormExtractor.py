import re
import fitz
import json
import logging
from pathlib import Path

# Import mappings for better field label extraction
from .mappings import resource_mappings, predicates_mapping, class_mappings


class PDFFormExtractor:
    """
    Extracts data from PDF forms, including finding text labels for interactive widgets.
    """

    def __init__(self, pdf_path: str, debug: bool = False):
        if not Path(pdf_path).is_file():
            raise FileNotFoundError(f"No file found at {pdf_path}")
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(self.pdf_path)
        self.results = {}

        # Initialize mappings for better field extraction
        self.resource_mappings = resource_mappings
        self.predicates_mapping = predicates_mapping
        self.class_mappings = class_mappings

        # logging setup
        self.debug = debug
        self.logger = logging.getLogger(__name__ + ".PDFFormExtractor")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%H:%M:%S",
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        self.logger.info(
            f"Opened PDF '{self.pdf_path.name}' with {len(self.doc)} pages"
        )

    def extract_with_labels(self) -> dict:
        """
        Primary extraction method that prioritizes finding labels for interactive fields.
        """
        self.logger.info("Starting extraction of interactive form fields with labels")

        has_interactive_fields = any(page.widgets() for page in self.doc)

        if not has_interactive_fields:
            self.logger.warning("No interactive form fields found in this PDF")
            return {}

        # First, collect all raw field data
        raw_fields = self._collect_raw_field_data()

        # Then, structure it into questions with options and answers
        structured_data = self._structure_form_data(raw_fields)

        # Post-process to merge duplicate questions with same question_text
        structured_data = self._merge_duplicate_questions(structured_data)

        # Validate extracted data against mappings
        if self.resource_mappings:
            structured_data = self._validate_against_mappings(structured_data)

        self.results = structured_data
        self.logger.info(
            "Extraction complete: %d fields -> %d questions (%d with answers)",
            structured_data.get("extraction_summary", {}).get("total_fields_found", 0),
            structured_data.get("total_questions", 0),
            structured_data.get("extraction_summary", {}).get(
                "questions_with_selections", 0
            ),
        )
        return self.results

    def _collect_raw_field_data(self) -> list:
        """
        Collects all raw field data from the PDF.
        """
        all_fields = []

        for page in self.doc:
            words_on_page = page.get_text("words")

            for widget in page.widgets():
                widget_info = self._get_widget_info(widget, words_on_page)
                widget_info["page"] = page.number + 1
                all_fields.append(widget_info)
                if self.debug:
                    self.logger.debug(
                        "Collected widget | page=%s name=%s type=%s value=%s label=%s field_label=%s",
                        widget_info.get("page"),
                        widget_info.get("name"),
                        widget_info.get("type"),
                        widget_info.get("value"),
                        widget_info.get("label"),
                        widget_info.get("field_label"),
                    )

        return all_fields

    def _structure_form_data(self, raw_fields: list) -> dict:
        """
        Structures the raw field data into a more readable format with questions, options, and answers.
        """
        from collections import defaultdict
        import re

        # Group fields by their base question (removing the suffix parts like _0_, _1_, etc.)
        question_groups = defaultdict(list)

        for field in raw_fields:
            field_name = field["name"]
            if not field_name:
                continue

            # Extract the base question by removing suffixes like _0_, _1_, _edit;_, etc.
            base_question = re.sub(r"_\d+_[^_]*$|_edit;_[^_]*$", "", field_name)
            question_groups[base_question].append(field)

        # Structure the data
        structured_questions = []

        for base_question, fields in question_groups.items():
            if not fields:
                continue

            # Prefer field_label from any field; fallback to extracted text from name
            first_field_label = next(
                (f.get("field_label") for f in fields if f.get("field_label")), None
            )
            question_text = first_field_label or self._extract_question_text(
                base_question
            )

            # Branch schema by field type
            group_types = {f.get("type") for f in fields}
            if self.debug:
                self.logger.debug(
                    "Group base=%s types=%s derived_question_text='%s'",
                    base_question,
                    ",".join(sorted([t or "" for t in group_types])),
                    question_text,
                )
            # If it's a single Text field, treat as free-text answer
            if len(fields) == 1 and next(iter(group_types)) == "Text":
                text_field = fields[0]
                question_data = {
                    # "question_id": base_question,
                    "question_text": question_text,
                    "type": "Text",
                    "answer": text_field.get("value") or "",
                    "field_name": text_field.get("name"),
                }
                structured_questions.append(question_data)
                if self.debug:
                    self.logger.debug(
                        "Text question formed | base=%s field=%s answer='%s'",
                        base_question,
                        text_field.get("name"),
                        question_data.get("answer"),
                    )
                continue
            # Otherwise, assume choice-type (Radio / Checkbox) with options
            selected_options = []
            all_options = []
            text_input_value = None

            # Get expected options from mappings to ensure completeness
            expected_options = self._get_expected_options_for_question(question_text)
            found_option_labels = set()
            option_labels_to_info = {}  # Track unique labels to avoid duplicates

            for field in fields:
                if field["type"] == "Text":
                    if field["label"] is None:
                        if not field["value"]:
                            continue
                        text_input_value = field["value"]

                # Enhance the field label using mappings
                enhanced_label = self._enhance_label_with_mappings(field["label"])

                option_info = {
                    "label": text_input_value or enhanced_label,
                    "field_name": field["name"],
                    "field_value": field["value"],
                    "is_selected": self._is_field_selected(field),
                }
                # Preserve provenance when an option originates from a Text field
                if field.get("type") == "Text":
                    option_info["source_type"] = "Text"

                option_label = option_info["label"]

                # Handle duplicate labels by merging their information
                if option_label in option_labels_to_info:
                    # Merge with existing option - prefer selected state and combine field values
                    existing_info = option_labels_to_info[option_label]
                    if option_info["is_selected"]:
                        existing_info["is_selected"] = True
                    # If this field has a value and existing doesn't, or vice versa, combine them
                    if option_info["field_value"] and not existing_info["field_value"]:
                        existing_info["field_value"] = option_info["field_value"]
                    elif option_info["field_value"] and existing_info["field_value"]:
                        # Both have values, combine them with a separator
                        existing_info["field_value"] = (
                            f"{existing_info['field_value']}, {option_info['field_value']}"
                        )
                    if self.debug:
                        self.logger.debug(
                            "Merged duplicate option label | label='%s' existing_field=%s new_field=%s",
                            option_label,
                            existing_info["field_name"],
                            option_info["field_name"],
                        )
                else:
                    # New unique label
                    option_labels_to_info[option_label] = option_info
                    found_option_labels.add(option_label)

                if self.debug:
                    self.logger.debug(
                        "Option | base=%s name=%s type=%s value=%s label=%s enhanced=%s selected=%s",
                        base_question,
                        field.get("name"),
                        field.get("type"),
                        field.get("value"),
                        field.get("label"),
                        enhanced_label,
                        option_info.get("is_selected"),
                    )

            # Convert the deduplicated options dictionary to list
            all_options = list(option_labels_to_info.values())

            # Rebuild selected_options from deduplicated options
            selected_options = [
                label
                for label, info in option_labels_to_info.items()
                if info["is_selected"]
            ]

            # Add missing expected options if mappings suggest they should be present
            if expected_options and self.debug:
                missing_options = set(expected_options) - found_option_labels
                if missing_options:
                    self.logger.debug(
                        "Question '%s' may be missing expected options: %s",
                        question_text,
                        list(missing_options)[:5],  # Show first 5
                    )

            # Create the structured question
            # Determine choice group type label
            group_type_label = (
                "RadioButton"
                if "RadioButton" in group_types
                else (
                    "CheckBox"
                    if "CheckBox" in group_types
                    else ",".join(sorted(group_types))
                )
            )
            question_data = {
                # "question_id": base_question,
                "question_text": question_text,
                "type": group_type_label,
                "selected_answers": selected_options if selected_options else ["None"],
                "all_options": [opt["label"] for opt in all_options],
                "options_details": all_options,
                "total_options": len(all_options),
            }

            structured_questions.append(question_data)
            if self.debug:
                self.logger.debug(
                    "Choice question formed | base=%s type=%s selected=%s total_options=%d",
                    base_question,
                    group_type_label,
                    ", ".join(selected_options) if selected_options else "None",
                    len(all_options),
                )

        # Derive summary counts with schema-aware logic
        def question_has_answer(q: dict) -> bool:
            qtype = q.get("type")
            if qtype == "Text":
                return bool(q.get("answer"))
            # Choice types
            selected = q.get("selected_answers")
            if selected is not None:
                return any(ans and ans != "None" for ans in selected)
            # Fallback using options_details
            for opt in q.get("options_details", []) or []:
                if opt.get("is_selected"):
                    return True
            return False

        questions_with_selections = sum(
            1 for q in structured_questions if question_has_answer(q)
        )

        result = {
            "pdf_name": self.pdf_path.name,
            "total_questions": len(structured_questions),
            "extraction_summary": {
                "total_fields_found": len(raw_fields),
                "questions_with_selections": questions_with_selections,
            },
            "questions": structured_questions,
        }
        if self.debug:
            self.logger.debug(
                "Structured %d questions (%d with answers) from %d fields",
                result["total_questions"],
                result["extraction_summary"]["questions_with_selections"],
                result["extraction_summary"]["total_fields_found"],
            )
        return result

    def _extract_question_text(self, base_question: str) -> str:
        """
        Extracts readable question text from the field name.
        """
        # Handle special cases first
        if base_question.startswith("_                             _"):
            return "Title and Authors"

        # Replace underscores with spaces and clean up
        question_text = base_question.replace("_", " ")

        # Remove hash-like suffixes (e.g., "3onV9GF51v2qn4B5z306pQ")
        question_text = re.sub(r"\s+[a-zA-Z0-9]{20,}\s*$", "", question_text)

        # Clean up Roman numeral patterns like "I 1 What RE Task..."
        question_text = re.sub(r"^(I+V*|V+I*)\s+(\d+)\s+", r"\1.\2. ", question_text)

        # Clean up multiple spaces
        question_text = re.sub(r"\s+", " ", question_text).strip()

        # Remove trailing incomplete words or artifacts
        question_text = re.sub(r"\s+[a-zA-Z]{1,3}$", "", question_text)

        # Capitalize first letter if it exists
        if question_text and len(question_text) > 1:
            question_text = question_text[0].upper() + question_text[1:]

        return question_text if question_text else "Question text not found"

    def _is_field_selected(self, field: dict) -> bool:
        """
        Determines if a field is selected based on its value and type.
        """
        field_value = field.get("value")
        field_type = field.get("type", "")

        if field_type == "RadioButton":
            # For radio buttons, check if value is not 'Off'
            selected = field_value not in ("Off", None, "")
            if self.debug:
                self.logger.debug(
                    "Selection check | type=RadioButton name=%s value=%s -> %s",
                    field.get("name"),
                    field_value,
                    selected,
                )
            return selected
        elif field_type == "CheckBox":
            # For checkboxes, check if value is not 'Off' or None
            selected = field_value not in ("Off", None, "")
            if self.debug:
                self.logger.debug(
                    "Selection check | type=CheckBox name=%s value=%s -> %s",
                    field.get("name"),
                    field_value,
                    selected,
                )
            return selected
        elif field_type == "Text":
            # For text fields, check if there's content
            selected = bool(field_value and field_value.strip())
            if self.debug:
                self.logger.debug(
                    "Selection check | type=Text name=%s value=%s -> %s",
                    field.get("name"),
                    field_value,
                    selected,
                )
            return selected

        return False

    def _get_widget_info(self, widget: fitz.Widget, words: list) -> dict:
        """
        Gets widget details and finds its associated text label.
        """
        widget_rect = widget.rect
        field_info = {
            "name": widget.field_name,
            "type": widget.field_type_string,
            "value": widget.field_value,
            # "rect": [round(c, 2) for c in widget_rect],
            "label": None,  # Default label
        }
        # Capture the form-defined field label if available (often holds the question text)
        try:
            field_info["field_label"] = widget.field_label
        except Exception:
            field_info["field_label"] = None

        # if widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
        #     field_info["is_checked"] = widget.is_checked
        # elif widget.field_type == fitz.PDF_WIDGET_TYPE_RADIOBUTTON:
        # # For radio buttons, is_checked tells if THIS specific button is selected
        # field_info["is_selected"] = widget.is_checked
        # # The group value shows which option was selected for the whole group
        # field_info["group_value"] = widget.field_value

        # Find the label for the widget using spatial analysis
        field_info["label"] = self._find_label_for_widget(widget_rect, words)
        if self.debug:
            self.logger.debug(
                "Widget info | name=%s type=%s value=%s field_label=%s label=%s rect=(%.1f,%.1f,%.1f,%.1f)",
                field_info.get("name"),
                field_info.get("type"),
                field_info.get("value"),
                field_info.get("field_label"),
                field_info.get("label"),
                widget_rect.x0,
                widget_rect.y0,
                widget_rect.x1,
                widget_rect.y1,
            )

        return field_info

    def _find_label_for_widget(self, widget_rect: fitz.Rect, words: list) -> str:
        """
        Searches for text labels to the right of a given widget's rectangle.
        Uses both vertical alignment and horizontal proximity to avoid picking up distant text.

        Args:
            widget_rect: The fitz.Rect object for the form widget.
            words: A list of words on the page from page.get_text("words").

        Returns:
            The found text label as a string, or None if no label is found.
        """
        # Define tolerances for alignment and proximity
        VERTICAL_TOLERANCE = 3  # pixels for vertical alignment
        MAX_HORIZONTAL_DISTANCE = 150  # maximum pixels to look to the right (balanced to capture full options but avoid cross-column contamination)

        widget_mid_y = (widget_rect.y0 + widget_rect.y1) / 2

        # Find all words that are vertically aligned and close horizontally
        candidate_words = []
        for word_rect in words:
            x0, y0, x1, y1, word_text = word_rect[:5]
            word_mid_y = (y0 + y1) / 2

            # Check for vertical alignment
            vertically_aligned = abs(word_mid_y - widget_mid_y) <= VERTICAL_TOLERANCE

            # Check if word is to the right but not too far
            horizontally_close = (x0 > widget_rect.x1) and (
                x0 - widget_rect.x1 <= MAX_HORIZONTAL_DISTANCE
            )

            if vertically_aligned and horizontally_close:
                candidate_words.append((x0, word_text))

        if self.debug:
            self.logger.debug(
                "Label candidates | count=%d (vertical_tol=%d, max_dx=%d)",
                len(candidate_words),
                VERTICAL_TOLERANCE,
                MAX_HORIZONTAL_DISTANCE,
            )

        if not candidate_words:
            return None

        # Sort by horizontal position
        candidate_words.sort(key=lambda x: x[0])

        # Stop collecting words if there's a large gap (indicating next column)
        label_words = []
        MAX_WORD_GAP = 50  # maximum gap between consecutive words in same label (increased to capture multi-word options)

        for i, (x_pos, word_text) in enumerate(candidate_words):
            if i == 0:
                label_words.append(word_text)
            else:
                prev_x = candidate_words[i - 1][0]
                gap = x_pos - prev_x

                # If gap is too large, we've likely moved to next column
                if gap > MAX_WORD_GAP:
                    break
                label_words.append(word_text)

        label = " ".join(label_words)

        # Enhance label using mappings if available
        enhanced_label = self._enhance_label_with_mappings(label)

        if self.debug:
            self.logger.debug(
                "Resolved label='%s' -> enhanced='%s'", label, enhanced_label
            )
        return enhanced_label or label

    def _enhance_label_with_mappings(self, label: str) -> str:
        """
        Enhances extracted labels using predefined mappings to fix incomplete or truncated text.

        Args:
            label: The raw extracted label text

        Returns:
            Enhanced label text if mapping found, otherwise original label
        """
        if not label or not self.resource_mappings:
            return label

        # Clean the label for comparison
        clean_label = label.strip()

        # Try to find a matching mapping key for this label
        for mapping_category, mappings in self.resource_mappings.items():
            # Direct match
            if clean_label in mappings:
                if self.debug:
                    self.logger.debug(
                        "Found direct mapping for '%s' in category '%s'",
                        clean_label,
                        mapping_category,
                    )
                return clean_label

            # Partial match - look for labels that start with our extracted text
            for mapped_label in mappings.keys():
                if mapped_label.startswith(clean_label) and len(clean_label) > 3:
                    if self.debug:
                        self.logger.debug(
                            "Found partial mapping '%s' -> '%s' in category '%s'",
                            clean_label,
                            mapped_label,
                            mapping_category,
                        )
                    return mapped_label

            # Fuzzy match for common truncation patterns
            for mapped_label in mappings.keys():
                # Check if our label is a truncated version of a mapped label
                if (
                    clean_label in mapped_label
                    and len(clean_label) > 5
                    and abs(len(mapped_label) - len(clean_label)) < 20
                ):
                    if self.debug:
                        self.logger.debug(
                            "Found fuzzy mapping '%s' -> '%s' in category '%s'",
                            clean_label,
                            mapped_label,
                            mapping_category,
                        )
                    return mapped_label

        return label

    def _get_expected_options_for_question(self, question_text: str) -> list:
        """
        Gets expected options for a question based on mappings.

        Args:
            question_text: The question text to find mappings for

        Returns:
            List of expected option labels
        """
        if not question_text or not self.predicates_mapping:
            return []

        # Try to match question text to predicate mappings
        for predicate_id, predicate_info in self.predicates_mapping.items():
            if predicate_info.get("description", "").lower() in question_text.lower():
                resource_key = predicate_info.get("resource_mapping_key")
                if resource_key and resource_key in self.resource_mappings:
                    options = list(self.resource_mappings[resource_key].keys())
                    if self.debug:
                        self.logger.debug(
                            "Found %d expected options for question '%s'",
                            len(options),
                            question_text,
                        )
                    return options

        return []

    def _validate_against_mappings(self, structured_data: dict) -> dict:
        """
        Validates extracted data against mappings and logs potential issues.

        Args:
            structured_data: The structured form data

        Returns:
            The validated structured data (with potential enhancements)
        """
        if not structured_data.get("questions"):
            return structured_data

        validation_summary = {
            "mapping_enhancements": 0,
            "potential_issues": [],
            "missing_options": 0,
        }

        for question in structured_data["questions"]:
            question_text = question.get("question_text", "")
            question_type = question.get("type", "")

            # Skip validation for text questions
            if question_type == "Text":
                continue

            # Check if we have expected options for this question
            expected_options = self._get_expected_options_for_question(question_text)
            if expected_options:
                found_options = set(question.get("all_options", []))
                missing_options = set(expected_options) - found_options

                if missing_options:
                    validation_summary["missing_options"] += len(missing_options)
                    if self.debug:
                        self.logger.debug(
                            "Question '%s' missing %d expected options: %s",
                            question_text[:50],
                            len(missing_options),
                            list(missing_options)[:3],  # Show first 3
                        )

                # Check for potential label enhancements
                for option in question.get("options_details", []):
                    original_label = option.get("label", "")
                    if original_label:
                        enhanced = self._enhance_label_with_mappings(original_label)
                        if enhanced != original_label:
                            validation_summary["mapping_enhancements"] += 1
                            if self.debug:
                                self.logger.debug(
                                    "Enhanced option label: '%s' -> '%s'",
                                    original_label,
                                    enhanced,
                                )

        # Add validation summary to results
        if (
            validation_summary["mapping_enhancements"] > 0
            or validation_summary["missing_options"] > 0
        ):
            structured_data["validation_summary"] = validation_summary
            if self.debug:
                self.logger.info(
                    "Validation complete: %d enhancements, %d missing options",
                    validation_summary["mapping_enhancements"],
                    validation_summary["missing_options"],
                )

        return structured_data

    def _merge_duplicate_questions(self, structured_data: dict) -> dict:
        """
        Post-processes the structured data to merge duplicate questions with the same question_text.
        When a question appears as both a choice-type (RadioButton/CheckBox) and a text field,
        appends the text field answer to the selected_answers of the choice-type question.
        Also injects a synthetic option into options_details with source_type="Text" so the
        origin of the merged answer is preserved.
        """
        questions = structured_data.get("questions", [])
        if not questions:
            return structured_data

        # Group questions by question_text
        question_groups = {}
        for question in questions:
            question_text = question.get("question_text", "")
            if question_text not in question_groups:
                question_groups[question_text] = []
            question_groups[question_text].append(question)

        # Process groups with multiple questions (duplicates)
        merged_questions = []
        for question_text, question_list in question_groups.items():
            if len(question_list) == 1:
                # No duplicates, keep as is
                merged_questions.append(question_list[0])
            else:
                # Found duplicates, merge them
                if self.debug:
                    self.logger.debug(
                        "Merging duplicate questions | text='%s' count=%d",
                        question_text,
                        len(question_list),
                    )
                merged_question = self._merge_question_group(question_list)
                merged_questions.append(merged_question)

        # Update the structured data with merged questions
        structured_data["questions"] = merged_questions
        structured_data["total_questions"] = len(merged_questions)

        # Recalculate questions_with_selections
        def question_has_answer(q: dict) -> bool:
            qtype = q.get("type")
            if qtype == "Text":
                return bool(q.get("answer"))
            # Choice types
            selected = q.get("selected_answers")
            if selected is not None:
                return any(ans and ans != "None" for ans in selected)
            # Fallback using options_details
            for opt in q.get("options_details", []) or []:
                if opt.get("is_selected"):
                    return True
            return False

        questions_with_selections = sum(
            1 for q in merged_questions if question_has_answer(q)
        )
        structured_data["extraction_summary"][
            "questions_with_selections"
        ] = questions_with_selections

        return structured_data

    def _merge_question_group(self, question_list: list) -> dict:
        """
        Merges a group of questions with the same question_text.
        Prioritizes choice-type questions (RadioButton/CheckBox) and appends text field answers.
        When merging a text field answer, additionally adds it as an option with
        source_type="Text" to options_details (and to all_options) and marks it selected.
        """
        # Find the choice-type question (RadioButton/CheckBox) and text field question
        choice_question = None
        text_question = None

        for question in question_list:
            question_type = question.get("type", "")
            if question_type in ["RadioButton", "CheckBox"]:
                choice_question = question
            elif question_type == "Text":
                text_question = question

        # If we have both choice and text questions, merge them
        if choice_question and text_question:
            # Get the text answer
            text_answer = text_question.get("answer", "").strip()

            # Append text answer to selected_answers if it's not empty
            if text_answer:
                selected_answers = choice_question.get("selected_answers", [])
                if selected_answers and selected_answers != ["None"]:
                    # Append the text answer to existing selected answers
                    selected_answers.append(text_answer)
                else:
                    # If no other selections, just use the text answer
                    selected_answers = [text_answer]
                choice_question["selected_answers"] = selected_answers

                # Ensure the merged text also appears as an option with provenance
                # 1) Add to all_options if not already present
                all_options = choice_question.get("all_options") or []
                if text_answer not in all_options:
                    all_options.append(text_answer)
                    choice_question["all_options"] = all_options

                # 2) Add to options_details with source_type indicating it came from Text
                options_details = choice_question.get("options_details") or []
                # Check if an option with the same label already exists
                existing_opt = next(
                    (o for o in options_details if o.get("label") == text_answer), None
                )
                if existing_opt:
                    # Mark as selected and keep any existing fields; annotate source_type if missing
                    existing_opt["is_selected"] = True
                    if not existing_opt.get("source_type"):
                        existing_opt["source_type"] = "Text"
                    if not existing_opt.get("field_value"):
                        existing_opt["field_value"] = text_answer
                else:
                    options_details.append(
                        {
                            "label": text_answer,
                            "field_name": text_question.get("field_name"),
                            "field_value": text_answer,
                            "is_selected": True,
                            "source_type": "Text",
                        }
                    )
                choice_question["options_details"] = options_details

                # 3) Update total_options to reflect any addition
                choice_question["total_options"] = len(
                    choice_question.get("options_details") or []
                )
                if self.debug:
                    self.logger.debug(
                        "Merged text answer into choices | text='%s' -> selected=%s (as option with source_type=Text)",
                        text_answer,
                        ", ".join(choice_question.get("selected_answers", []))
                        or "None",
                    )

            return choice_question
        else:
            # If only one type exists, return the first one
            return question_list[0]

    def to_json(self, indent: int = 2) -> str:
        """
        Converts the extracted results dictionary to a JSON formatted string.
        """
        return json.dumps(self.results, indent=indent, ensure_ascii=False)
