"""
ORKG Native Template Creation Module

This module creates proper ORKG templates that can be materialized and used
according to the ORKG template system documentation.
"""

import json
from .orkg_connection import ORKGConnection
from .config import PREDICATES, CLASSES, DATATYPES


class ORKGTemplateCreator:
    """Handles creation of native ORKG templates from JSON data"""

    def __init__(self):
        """Initialize with ORKG connection"""
        self.orkg_conn = ORKGConnection()

    def create_native_template_from_json(self, json_file_path, template_label):
        """
        Create a native ORKG template from a JSON file that can be properly materialized

        Args:
            json_file_path (str): Path to the JSON file containing form data
            template_label (str): Label for the new template

        Returns:
            dict: Template information including ID and materialization status
        """
        print(f"Starting native ORKG template creation for: '{template_label}'")

        # Load JSON data
        data = self._load_json_data(json_file_path)

        # Create the template structure
        template_info = self._create_template_structure(template_label, data)

        # Try to materialize the template
        materialization_result = self._materialize_template(template_info["id"])

        print(f"Native ORKG template creation for '{template_label}' is complete!")
        print(
            f"Template URL: https://incubating.orkg.org/template/{template_info['id']}"
        )

        return {
            "id": template_info["id"],
            "label": template_label,
            "materialized": materialization_result,
            "parameters": template_info["parameters"],
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

    def _create_template_structure(self, template_label, data):
        """
        Create the proper ORKG template structure

        This creates a template that follows ORKG's native template system
        rather than just SHACL shapes
        """
        # Create main template resource
        template_id = self.orkg_conn.generate_unique_id("T")
        template_resource_id = self.orkg_conn.create_resource(
            label=template_label,
            classes=[],  # Template class doesn't exist in ORKG, use generic resource
            custom_id=template_id,
        )

        # Create target class for the template
        target_class_id = self.orkg_conn.generate_unique_id("C")
        target_class_resource_id = self.orkg_conn.create_or_find_class(
            f"{template_label} Instance", custom_id=target_class_id
        )

        # Link template to target class
        self.orkg_conn.add_statement(
            subject_id=template_resource_id,
            predicate_id="hasTargetClass",  # ORKG-specific predicate
            object_id=target_class_resource_id,
        )

        # Process questions and create template parameters
        parameters = self._create_template_parameters(
            data, template_resource_id, template_label
        )

        print(
            f"Created native ORKG template '{template_label}' with ID: {template_resource_id}"
        )
        print(f"Created {len(parameters)} template parameters")

        return {
            "id": template_resource_id,
            "target_class_id": target_class_resource_id,
            "parameters": parameters,
        }

    def _create_template_parameters(self, data, template_id, template_label):
        """Create template parameters for each question"""
        questions = data.get("questions", [])
        parameters = []

        for i, question in enumerate(questions):
            question_text = question.get("question_text")
            question_type = question.get("type")

            # Skip internal or irrelevant fields
            if not self._is_valid_question(question_text, question_type):
                continue

            print(f"Creating template parameter: '{question_text}'")
            parameter_info = self._create_template_parameter(
                question, template_id, template_label, i
            )
            parameters.append(parameter_info)

        return parameters

    def _create_template_parameter(self, question, template_id, template_label, order):
        """Create a single template parameter"""
        question_text = question.get("question_text")
        question_type = question.get("type")

        # Create the parameter resource
        param_id = self.orkg_conn.generate_unique_id("TP")
        param_resource_id = self.orkg_conn.create_resource(
            label=f"Parameter: {question_text}",
            classes=[],  # TemplateParameter class doesn't exist, use generic resource
            custom_id=param_id,
        )

        # Create or find the predicate for this parameter
        predicate_id = self.orkg_conn.generate_unique_id("P")
        actual_predicate_id = self.orkg_conn.create_or_find_predicate(
            question_text, custom_id=predicate_id
        )

        # Link parameter to template
        self.orkg_conn.add_statement(
            subject_id=template_id,
            predicate_id="hasParameter",
            object_id=param_resource_id,
        )

        # Set parameter properties
        self.orkg_conn.add_statement(
            subject_id=param_resource_id,
            predicate_id="hasProperty",
            object_id=actual_predicate_id,
        )

        # Set parameter order
        order_literal_id = self.orkg_conn.create_literal(
            str(order), datatype="xsd:integer"
        )
        self.orkg_conn.add_statement(
            subject_id=param_resource_id,
            predicate_id="hasOrder",
            object_id=order_literal_id,
        )

        # Set parameter type and constraints based on question type
        self._set_parameter_constraints(param_resource_id, question, template_label)

        return {
            "id": param_resource_id,
            "predicate_id": actual_predicate_id,
            "question_text": question_text,
            "question_type": question_type,
            "order": order,
        }

    def _set_parameter_constraints(self, param_resource_id, question, template_label):
        """Set constraints for the template parameter based on question type"""
        question_text = question.get("question_text")
        question_type = question.get("type")

        if question_type == "Text":
            # Set datatype constraint
            self.orkg_conn.add_statement(
                subject_id=param_resource_id,
                predicate_id="hasDatatype",
                object_id="String",
            )
            print(f"    -> Set parameter datatype to 'String'")

        elif question_type in ["RadioButton", "CheckBox"]:
            # Create class constraint for options
            options_class_label = f"{template_label}: {question_text} Options"
            options_class_id = self.orkg_conn.generate_unique_id("OC")
            actual_options_class_id = self.orkg_conn.create_or_find_class(
                options_class_label, custom_id=options_class_id
            )

            # Set class constraint
            self.orkg_conn.add_statement(
                subject_id=param_resource_id,
                predicate_id="hasClass",
                object_id=actual_options_class_id,
            )

            # Set cardinality for RadioButton (single selection)
            if question_type == "RadioButton":
                max_count_literal_id = self.orkg_conn.create_literal(
                    "1", datatype="xsd:integer"
                )
                self.orkg_conn.add_statement(
                    subject_id=param_resource_id,
                    predicate_id="hasMaxCount",
                    object_id=max_count_literal_id,
                )

            # Create option resources
            self._create_option_resources(question, actual_options_class_id)
            print(f"    -> Set parameter class to '{options_class_label}'")

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
            print(f"    -> Created {created_count} option resources")

    def _is_valid_question(self, question_text, question_type):
        """Check if a question should be processed"""
        if not question_text or not question_type:
            return False
        if question_text == "Fc-int01-generateAppearances":
            return False
        return True

    def _materialize_template(self, template_id):
        """
        Attempt to materialize the template using ORKG's template system

        Note: This may require the template to be properly structured
        according to ORKG's template schema
        """
        try:
            # Try to materialize the template
            result = self.orkg_conn.orkg.templates.materialize_template(template_id)
            print(f"✅ Template {template_id} materialized successfully")
            return True
        except Exception as e:
            print(f"⚠️  Template materialization failed: {e}")
            print(
                "Template created but may need manual materialization in ORKG interface"
            )
            return False

    def create_template_instance(self, template_id, instance_data):
        """
        Create an instance of the materialized template

        Args:
            template_id (str): The ID of the materialized template
            instance_data (dict): Data to populate the instance

        Returns:
            str: The ID of the created instance
        """
        try:
            # Try to use the materialized template to create an instance
            # This would work if the template was properly materialized
            template_function = getattr(
                self.orkg_conn.orkg.templates, f"template_{template_id}"
            )
            instance = template_function(**instance_data)
            instance_id = instance.save()
            print(f"✅ Created template instance with ID: {instance_id}")
            return instance_id
        except Exception as e:
            print(f"⚠️  Template instance creation failed: {e}")
            print(
                "You may need to create instances manually through the ORKG interface"
            )
            return None
