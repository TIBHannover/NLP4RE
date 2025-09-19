"""
ORKG Template Creation Module
"""

import json
from .orkg_connection import ORKGConnection
from .config import PREDICATES, CLASSES, DATATYPES
from .orkg_template_creator import ORKGTemplateCreator


class TemplateCreator:
    """Handles creation of ORKG templates from JSON data"""

    def __init__(self):
        """Initialize with ORKG connection"""
        self.orkg_conn = ORKGConnection()
        self.native_creator = ORKGTemplateCreator()

    def create_template_from_json(self, json_file_path, template_label):
        """
        Create an ORKG template from a JSON file using the proper ORKG template API

        Args:
            json_file_path (str): Path to the JSON file containing form data
            template_label (str): Label for the new template

        Returns:
            str: The ID of the created template
        """
        print(f"Starting template creation for: '{template_label}'")

        # Load JSON data
        data = self._load_json_data(json_file_path)

        # Create main class for the template
        main_class_id = self._create_main_class(template_label)

        # Build template data using ORKG template API format
        template_data = self._build_template_data(data, template_label, main_class_id)

        # Create template using ORKG template API
        template_id = self.orkg_conn.create_template(template_data)

        print(f"Template creation for '{template_label}' is complete!")
        print(f"Template URL: https://incubating.orkg.org/template/{template_id}")

        return template_id

    def create_native_template_from_json(self, json_file_path, template_label):
        """
        Create a native ORKG template that can be properly materialized

        This method creates templates using ORKG's native template system
        instead of just SHACL shapes, allowing for proper materialization
        and instance creation.

        Args:
            json_file_path (str): Path to the JSON file containing form data
            template_label (str): Label for the new template

        Returns:
            dict: Template information including ID and materialization status
        """
        return self.native_creator.create_native_template_from_json(
            json_file_path, template_label
        )

    def create_hybrid_template_from_json(self, json_file_path, template_label):
        """
        Create both SHACL-based and native ORKG templates for maximum compatibility

        This creates both types of templates:
        1. SHACL-based template (NodeShape/PropertyShape) for validation
        2. Native ORKG template for materialization and instance creation

        Args:
            json_file_path (str): Path to the JSON file containing form data
            template_label (str): Label for the new template

        Returns:
            dict: Information about both created templates
        """
        print(f"Creating hybrid template approach for: '{template_label}'")

        # Create SHACL-based template
        shacl_template_id = self.create_template_from_json(
            json_file_path, f"{template_label} (SHACL)"
        )

        # Create native ORKG template
        native_template_info = self.native_creator.create_native_template_from_json(
            json_file_path, f"{template_label} (Native)"
        )

        return {
            "shacl_template": {
                "id": shacl_template_id,
                "label": f"{template_label} (SHACL)",
                "type": "SHACL",
                "url": f"https://incubating.orkg.org/template/{shacl_template_id}",
            },
            "native_template": {
                "id": native_template_info["id"],
                "label": native_template_info["label"],
                "type": "Native ORKG",
                "materialized": native_template_info["materialized"],
                "parameters": native_template_info["parameters"],
                "url": f"https://incubating.orkg.org/template/{native_template_info['id']}",
            },
        }

    def _load_json_data(self, json_file_path):
        """Load and validate JSON data"""
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            raise FileNotFoundError(f"The file '{json_file_path}' was not found.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in '{json_file_path}': {e}")

    def _create_main_class(self, template_label):
        """Create the main class for the template"""
        class_id = self.orkg_conn.generate_unique_id("C")
        return self.orkg_conn.create_or_find_class(template_label, custom_id=class_id)

    def _build_template_data(self, data, template_label, target_class_id):
        """
        Build template data in ORKG template API format

        Args:
            data (dict): JSON data with questions
            template_label (str): Label for the template
            target_class_id (str): ID of the target class

        Returns:
            dict: Template data in ORKG API format
        """
        questions = data.get("questions", [])
        properties = []

        for question in questions:
            question_text = question.get("question_text")
            question_type = question.get("type")

            # Skip internal or irrelevant fields
            if not self._is_valid_question(question_text, question_type):
                continue

            print(f"Processing question: '{question_text}'")

            # Create predicate for this property
            predicate_id = self.orkg_conn.create_or_find_predicate(question_text)

            # Build property data based on question type
            property_data = {
                "label": question_text,
                "path": predicate_id,
                "min_count": 0,  # Optional by default
                "max_count": None,  # No limit by default
            }

            if question_type == "Text":
                property_data["datatype"] = "String"
                print(f"    -> Set property type to 'String'")

            elif question_type == "RadioButton":
                # For radio buttons, create class and set max_count to 1
                options_class_id = self._create_options_class(question, template_label)
                property_data["class"] = options_class_id
                property_data["max_count"] = 1  # Single selection
                print(f"    -> Set property type to class with single selection")

            elif question_type == "CheckBox":
                # For checkboxes, create class but allow multiple selections
                options_class_id = self._create_options_class(question, template_label)
                property_data["class"] = options_class_id
                print(f"    -> Set property type to class with multiple selection")

            properties.append(property_data)

        # Build the complete template data
        template_data = {
            "label": template_label,
            "description": f"Template for {template_label} with {len(properties)} properties",
            "formatted_label": "{P32}",  # Default formatted label
            "target_class": target_class_id,
            "relations": {
                "research_fields": [],
                "research_problems": [],
                "predicate": "P32",  # Default predicate
            },
            "properties": properties,
            "is_closed": False,  # Allow additional properties
            "organizations": [],  # Empty list for organizations
            "observatories": [],  # Empty list for observatories
            "extraction_method": "MANUAL",
        }

        return template_data

    def _create_options_class(self, question, template_label):
        """
        Create a class for question options and populate it with option resources

        Args:
            question (dict): Question data with options
            template_label (str): Template label for naming

        Returns:
            str: ID of the created options class
        """
        question_text = question.get("question_text")
        options_class_label = f"{template_label}: {question_text}"

        # Create the options class
        options_class_id = self.orkg_conn.generate_unique_id("OC")
        actual_options_class_id = self.orkg_conn.create_or_find_class(
            options_class_label, custom_id=options_class_id
        )

        # Create resources for each option
        all_options = question.get("all_options", [])
        created_count = 0

        for option_label in all_options:
            if isinstance(option_label, str) and option_label.strip():
                option_resource_id = self.orkg_conn.generate_unique_id("O")
                self.orkg_conn.create_resource(
                    label=option_label,
                    classes=[actual_options_class_id],
                    custom_id=option_resource_id,
                )
                created_count += 1

        if created_count > 0:
            print(f"    -> Created {created_count} option resources")

        return actual_options_class_id

    def _process_questions_shacl(self, data, template_id, template_label):
        """Process all questions from the JSON data using SHACL approach"""
        questions = data.get("questions", [])

        for question in questions:
            question_text = question.get("question_text")
            question_type = question.get("type")

            # Skip internal or irrelevant fields
            if not self._is_valid_question(question_text, question_type):
                continue

            print(f"Processing question: '{question_text}'")
            self._create_property_shape(question, template_id, template_label)

    def _create_template_resource(self, template_label, main_class_id):
        """Create the template resource (NodeShape)"""
        template_id = self.orkg_conn.generate_unique_id("T")
        template_resource_id = self.orkg_conn.create_resource(
            label=template_label, classes=[CLASSES["NodeShape"]], custom_id=template_id
        )

        # Link template to main class
        self.orkg_conn.add_statement(
            subject_id=template_resource_id,
            predicate_id=PREDICATES["sh:targetClass"],
            object_id=main_class_id,
        )

        print(
            f"Created Template (NodeShape) '{template_label}' with ID: {template_resource_id}"
        )
        return template_resource_id

    def _process_questions(self, data, template_id, template_label):
        """Process all questions from the JSON data"""
        questions = data.get("questions", [])

        for question in questions:
            question_text = question.get("question_text")
            question_type = question.get("type")

            # Skip internal or irrelevant fields
            if not self._is_valid_question(question_text, question_type):
                continue

            print(f"Processing question: '{question_text}'")
            self._create_property_shape(question, template_id, template_label)

    def _is_valid_question(self, question_text, question_type):
        """Check if a question should be processed"""
        if not question_text or not question_type:
            return False
        if question_text == "Fc-int01-generateAppearances":
            return False
        return True

    def _create_property_shape(self, question, template_id, template_label):
        """Create a PropertyShape for a question"""
        question_text = question.get("question_text")
        question_type = question.get("type")

        # Create predicate with custom ID
        predicate_id = self.orkg_conn.generate_unique_id("P")
        actual_predicate_id = self.orkg_conn.create_or_find_predicate(
            question_text, custom_id=predicate_id
        )

        # Create PropertyShape with custom ID
        property_shape_id = self.orkg_conn.generate_unique_id("PS")
        shape_label = f"Shape for: {question_text}"
        actual_shape_id = self.orkg_conn.create_resource(
            label=shape_label,
            classes=[CLASSES["PropertyShape"]],
            custom_id=property_shape_id,
        )

        # Link template to property shape and shape to predicate
        self.orkg_conn.add_statement(
            subject_id=template_id,
            predicate_id=PREDICATES["sh:property"],
            object_id=actual_shape_id,
        )
        self.orkg_conn.add_statement(
            subject_id=actual_shape_id,
            predicate_id=PREDICATES["sh:path"],
            object_id=actual_predicate_id,
        )

        # Set value type based on question type
        self._set_value_type(question, actual_shape_id, template_label)

    def _set_value_type(self, question, property_shape_id, template_label):
        """Set the value type for a PropertyShape based on question type"""
        question_text = question.get("question_text")
        question_type = question.get("type")

        if question_type == "Text":
            self.orkg_conn.add_statement(
                subject_id=property_shape_id,
                predicate_id=PREDICATES["sh:datatype"],
                object_id=DATATYPES["String"],
            )
            print(f"    -> Set value type to 'String'")

        elif question_type in ["RadioButton", "CheckBox"]:
            self._handle_option_based_question(
                question, property_shape_id, template_label
            )

    def _handle_option_based_question(
        self, question, property_shape_id, template_label
    ):
        """Handle RadioButton and CheckBox type questions"""
        question_text = question.get("question_text")
        question_type = question.get("type")

        # Create options class with custom ID
        options_class_label = f"{template_label}: {question_text}"
        options_class_id = self.orkg_conn.generate_unique_id("OC")
        actual_options_class_id = self.orkg_conn.create_or_find_class(
            options_class_label, custom_id=options_class_id
        )

        # Link PropertyShape to options class
        self.orkg_conn.add_statement(
            subject_id=property_shape_id,
            predicate_id=PREDICATES["sh:class"],
            object_id=actual_options_class_id,
        )
        print(f"    -> Set value type to class '{options_class_label}'")

        # Set max count for RadioButton (single selection)
        if question_type == "RadioButton":
            self._set_max_count_constraint(property_shape_id)

        # Create resources for each option
        self._create_option_resources(question, actual_options_class_id)

    def _set_max_count_constraint(self, property_shape_id):
        """Set maxCount constraint for single-selection questions"""
        literal_id = self.orkg_conn.generate_unique_id("L")
        max_count_literal_id = self.orkg_conn.create_literal(
            label="1", datatype=DATATYPES["xsd:integer"], custom_id=literal_id
        )

        self.orkg_conn.add_statement(
            subject_id=property_shape_id,
            predicate_id=PREDICATES["sh:maxCount"],
            object_id=max_count_literal_id,
        )

    def _create_option_resources(self, question, options_class_id):
        """Create resources for each option in RadioButton/CheckBox questions"""
        all_options = question.get("all_options", [])
        created_count = 0

        for option_label in all_options:
            if isinstance(option_label, str) and option_label.strip():
                option_resource_id = self.orkg_conn.generate_unique_id("O")
                self.orkg_conn.create_resource(
                    label=option_label,
                    classes=[options_class_id],
                    custom_id=option_resource_id,
                )
                created_count += 1

        if created_count > 0:
            print(f"    -> Created {created_count} resources for the options class.")

    def add_predicate_to_template(
        self, template_id, predicate_label="Sample predicate: Notes"
    ):
        """
        Add a sample predicate to an existing template

        Args:
            template_id (str): The ID of the template to modify
            predicate_label (str): The label for the new predicate

        Returns:
            str: The ID of the created PropertyShape
        """
        # Create predicate with custom ID
        predicate_id = self.orkg_conn.generate_unique_id("P")
        actual_predicate_id = self.orkg_conn.create_or_find_predicate(
            predicate_label, custom_id=predicate_id
        )

        # Create PropertyShape with custom ID
        property_shape_id = self.orkg_conn.generate_unique_id("PS")
        shape_label = f"Shape for: {predicate_label}"
        actual_shape_id = self.orkg_conn.create_resource(
            label=shape_label,
            classes=[CLASSES["PropertyShape"]],
            custom_id=property_shape_id,
        )

        # Link template to property shape and shape to predicate
        self.orkg_conn.add_statement(
            subject_id=template_id,
            predicate_id=PREDICATES["sh:property"],
            object_id=actual_shape_id,
        )
        self.orkg_conn.add_statement(
            subject_id=actual_shape_id,
            predicate_id=PREDICATES["sh:path"],
            object_id=actual_predicate_id,
        )

        # Set value type to String
        self.orkg_conn.add_statement(
            subject_id=actual_shape_id,
            predicate_id=PREDICATES["sh:datatype"],
            object_id=DATATYPES["String"],
        )

        print(
            f"Added predicate '{predicate_label}' to template {template_id} (PropertyShape: {actual_shape_id})."
        )
        return actual_shape_id
