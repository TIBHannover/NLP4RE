import re
import fitz
import json
from pathlib import Path


class PDFFormExtractor:
    """
    Extracts data from PDF forms, including finding text labels for interactive widgets.
    """

    def __init__(self, pdf_path: str):
        if not Path(pdf_path).is_file():
            raise FileNotFoundError(f"No file found at {pdf_path}")
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(self.pdf_path)
        self.results = {}
        print(f"Successfully opened '{self.pdf_path.name}'")

    def extract_with_labels(self) -> dict:
        """
        Primary extraction method that prioritizes finding labels for interactive fields.
        """
        print("--- Starting extraction of interactive form fields with labels ---")

        has_interactive_fields = any(page.widgets() for page in self.doc)

        if not has_interactive_fields:
            print("No interactive form fields found in this PDF.")
            return {}

        # First, collect all raw field data
        raw_fields = self._collect_raw_field_data()

        # Then, structure it into questions with options and answers
        structured_data = self._structure_form_data(raw_fields)

        self.results = structured_data
        print("--- Extraction Complete ---")
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
                continue

            # Otherwise, assume choice-type (Radio / Checkbox) with options
            selected_options = []
            all_options = []
            text_input_value = None
            for field in fields:
                if field["type"] == "Text":
                    if field["label"] is None:
                        if not field["value"]:
                            continue
                        text_input_value = field["value"]
                option_info = {
                    "label": text_input_value or field["label"],
                    "field_name": field["name"],
                    "field_value": field["value"],
                    "is_selected": self._is_field_selected(field),
                }

                all_options.append(option_info)

                if option_info["is_selected"]:
                    selected_options.append(option_info["label"])

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

        return {
            "pdf_name": self.pdf_path.name,
            "total_questions": len(structured_questions),
            "extraction_summary": {
                "total_fields_found": len(raw_fields),
                "questions_with_selections": questions_with_selections,
            },
            "questions": structured_questions,
        }

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
            return field_value not in ("Off", None, "")
        elif field_type == "CheckBox":
            # For checkboxes, check if value is not 'Off' or None
            return field_value not in ("Off", None, "")
        elif field_type == "Text":
            # For text fields, check if there's content
            return bool(field_value and field_value.strip())

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

        return " ".join(label_words)

    def to_json(self, indent: int = 2) -> str:
        """
        Converts the extracted results dictionary to a JSON formatted string.
        """
        return json.dumps(self.results, indent=indent, ensure_ascii=False)
