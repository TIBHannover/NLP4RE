#!/usr/bin/env python3
"""
Simple JSON to ORKG Template Instance Creator

This script creates template instances from JSON survey data.
Maps JSON questions to template fields and creates properly typed resources.
"""

import json
from orkg import ORKG
from typing import Dict, Any, List, Optional
from scripts.config import ORKG_HOST, ORKG_USERNAME, ORKG_PASSWORD


class TemplateInstanceCreator:
    """Creates template instances from JSON survey data"""

    def __init__(self):
        """Initialize ORKG connection"""
        self.orkg = ORKG(
            host=ORKG_HOST,
            creds=(ORKG_USERNAME, ORKG_PASSWORD),
        )
        print("✅ Connected to ORKG")

        self.template_id = "R909131"
        self.target_class_id = "C112026"

        # Field mappings: template field -> JSON questions
        self.field_mappings = {
            "_problem_tackled": {
                "predicate": "P171101",
                "questions": ["I.1. What RE Task is your study addressing?"],
            },
            "solution_proposed": {
                "predicate": "P171100",
                "questions": [
                    "II.1. What types of NLP task is your study tackling?",
                    # "VI.1. What is the type of proposed solution?",
                    # "VI.2. What algorithms are used in the tool?",
                ],
            },
            "input_granularity": {
                "predicate": "P171099",
                "questions": [
                    "III.1. What is the input of your NLP task?",
                    # "III.4. What is the level of granularity of the extracted elements?",
                ],
            },
            "output_type": {
                "predicate": "P145054",
                "questions": [
                    "III.2. What type of classification is the study about?",
                    # "III.6. What is the type of output?",
                    # "III.7. What is the translation mapping cardinality between initial input and final output?",
                ],
            },
            "data_and_dataset": {
                "predicate": "P171104",
                "template_id": "R909134",
                "template_properties": {
                    "P171088": "number of items",
                    "P70001": "time interval",
                    "P17001": "datas source",
                    "P171086": "level of abstraction of data",
                    "P44150": "data format",
                    "P171092": "Heterogeneity",
                    "P171093": "number of data sources",
                    "P171094": "Dataset publicly available",
                    "P171095": "Dataset available under the license",
                    "url": "url",
                },
                "questions": [
                    "IV.1. How many data items do you process?",
                    # "IV.2. In which year or interval of year were the data produced?",
                    # "IV.3. What is the source of the data?",
                    # "IV.5. What is the format of the data?",
                    # "IV.8. Please list which domains your data belongs to",
                    # "IV.10. Is the dataset publicly available?",
                ],
            },
            "annotation_process": {
                "predicate": "P171102",
                "template_id": "R909122",
                "template_properties": {
                    "P171084": "number of involved annotators",
                    "P171083": "Entries annotation method",
                    "P171082": "Average annotator domain experience level",
                    "P171089": "Annotator identity",
                    "P171090": "Annotation scheme establishment method",
                    "P171091": "written guidelines public availability",
                    "P171085": "additional supporting information shared",
                    "P171087": "fatigue mitigation techniques employed",
                },
                "questions": [
                    "V.1. How many annotators have been involved?",
                    # "V.2. How are the entries annotated?",
                    # "V.3. What is the average level of application domain experience of the annotators?",
                    # "V.4. Who are the annotators?",
                    # "V.5. How was the annotation scheme established among the annotators?",
                    # "V.10. How were conflicts resolved?",
                ],
            },
            "tool": {
                "predicate": "P15292",
                "template_id": "R909132",
                "template_properties": {
                    "P171103": "proposed solution type",
                    "P71039": "used algorithms",
                    "P171107": "released items",
                    "P171105": "tool running requirements",
                    "P171106": "tool documentation type",
                    "P171110": "tool dependencies",
                    "P171109": "tool release method",
                    "P171108": "tool license",
                    "url": "url",
                },
                "questions": [
                    "VI.3. What has been released?",
                    # "VI.4. What needs to be done for running the tool?",
                    # "VI.5. What type of documentation has been provided alongside the tool?",
                    # "VI.6. What type of dependencies does the tool have?",
                    # "VI.7. How is the tool released?",
                ],
            },
            "evaluation": {
                "predicate": "P34",
                "template_id": "R909130",
                "template_properties": {
                    "P41532": "Evaluation metrics",
                    "P171096": "validation procedure",
                    "P171097": "baseline comparison",
                    "P171098": "baseline comparison details",
                },
                "questions": [
                    "VII.1. What metrics are used to evaluate the approach(es)?",
                    # "VII.2. What is the validation procedure?",
                    # "VII.3. What baseline do you compare against?",
                    # "VII.4. Please provide more details about the baseline you compare against",
                ],
            },
        }

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

    def extract_answer_from_question(self, question_data: Dict) -> str:
        """Extract the answer from a question data structure"""
        answers = []

        # Check if question has any meaningful content
        question_text = question_data.get("question_text", "").strip()
        if not question_text:
            return ""

        # Extract direct text answers
        if question_data.get("answer"):
            answer = question_data["answer"].strip()
            if answer:
                answers.append(answer)

        # Extract selected answers from multiple choice
        if question_data.get("selected_answers"):
            for answer in question_data["selected_answers"]:
                if answer and answer.strip():
                    answers.append(answer.strip())

        # Extract from options details
        if question_data.get("options_details"):
            for option in question_data["options_details"]:
                if option.get("is_selected"):
                    # Add label if it exists and is not empty
                    if option.get("label") and option["label"].strip():
                        answers.append(option["label"].strip())

                    # Add field value if it exists and is meaningful
                    field_value = option.get("field_value", "")
                    if (
                        field_value
                        and field_value.strip()
                        and field_value not in ["Yes", "Off", "", "None"]
                    ):
                        answers.append(field_value.strip())

        # Extract text input value for "Other/Comments" fields
        if question_data.get("text_input_value"):
            text_input = question_data["text_input_value"].strip()
            if text_input and text_input not in ["", "None"]:
                answers.append(text_input)

        # Filter out empty answers and return
        filtered_answers = [ans for ans in answers if ans and ans.strip()]
        return "; ".join(filtered_answers) if filtered_answers else ""

    def extract_field_data(self, json_data: Dict[str, Any], field_name: str) -> str:
        """Extract data for a specific template field"""
        questions = json_data.get("questions", [])
        field_values = []

        for target_question in self.field_mappings[field_name]["questions"]:
            # Skip if target question is empty
            if not target_question.strip():
                continue

            for question in questions:
                question_text = question.get("question_text", "")
                if not question_text.strip():
                    continue

                if target_question.lower() in question_text.lower():
                    answer = self.extract_answer_from_question(question)
                    # Only add non-empty answers
                    if answer and answer.strip():
                        field_values.append(answer.strip())

        # Filter out empty values and return
        filtered_values = [val for val in field_values if val and val.strip()]
        return " | ".join(filtered_values) if filtered_values else ""

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

    def create_subtemplate_instance(
        self, field_name: str, json_data: Dict[str, Any], paper_title: str
    ) -> Optional[str]:
        """Create a subtemplate instance for fields that have template_id"""
        field_config = self.field_mappings[field_name]

        if "template_id" not in field_config:
            return None

        template_id = field_config["template_id"]
        template_properties = field_config.get("template_properties", {})

        # Define target classes for each subtemplate
        subtemplate_classes = {
            "data_and_dataset": ["C112028"],  # RE Data and Dataset class
            "annotation_process": ["C112025"],  # RE Annotation Process class
            "tool": ["C112027"],  # RE Tool class
            "evaluation": ["C112029"],  # RE Evaluation class
        }

        try:
            # Get the appropriate class for this subtemplate
            target_classes = subtemplate_classes.get(field_name, [])

            # Create the subtemplate instance with proper class
            instance_response = self.orkg.resources.add(
                label=f"{paper_title} - {field_name}",
                classes=target_classes,
            )

            if not instance_response.succeeded:
                print(f"  ❌ Failed to create subtemplate instance")
                return None

            subtemplate_id = instance_response.content["id"]
            print(f"  ✅ Created subtemplate instance: {subtemplate_id}")

            try:
                tp = self.orkg.templates
                tp.materialize_template(template_id)
                print(f"    ✅ Materialized subtemplate {template_id}")
            except Exception as e:
                print(f"    ⚠️ Could not materialize subtemplate: {e}")

            # Map specific questions to subtemplate properties
            self.populate_subtemplate_properties(
                subtemplate_id, field_name, json_data, template_properties
            )

            return subtemplate_id

        except Exception as e:
            print(f"  ❌ Error creating subtemplate: {e}")
            return None

    def populate_subtemplate_properties(
        self,
        subtemplate_id: str,
        field_name: str,
        json_data: Dict[str, Any],
        template_properties: Dict[str, str],
    ):
        """Populate subtemplate properties with specific data"""
        questions = json_data.get("questions", [])

        # Define mappings from JSON questions to subtemplate properties
        question_to_property_mappings = {
            "data_and_dataset": {
                "IV.1. How many data items do you process?": "P171088",  # number of items
                "IV.2. In which year or interval of year were the data produced?": "P70001",  # time interval
                "IV.3. What is the source of the data?": "P17001",  # data source
                "IV.4. What is the level of abstraction of the data?": "P171086",  # level of abstraction
                "IV.5. What is the format of the data?": "P44150",  # data format
                "IV.10. Is the dataset publicly available?": "P171094",  # dataset publicly available
            },
            "annotation_process": {
                "V.1. How many annotators have been involved?": "P171084",  # number of involved annotators
                "V.2. How are the entries annotated?": "P171083",  # entries annotation method
                "V.3. What is the average level of application domain experience of the annotators?": "P171082",  # average annotator domain experience
                "V.4. Who are the annotators?": "P171089",  # annotator identity
                "V.5. How was the annotation scheme established among the annotators?": "P171090",  # annotation scheme establishment
                "V.6. Did you make the written guidelines public?": "P171091",  # written guidelines public availability
                "V.7. Did you share other information that could support the annotators?": "P171085",  # additional supporting information
                "V.8. Did you employ techniques to mitigate fatigue effects?": "P171087",  # fatigue mitigation techniques
            },
            "tool": {
                "VI.1. What is the type of proposed solution?": "P171103",  # proposed solution type
                "VI.2. What algorithms are used in the tool?": "P71039",  # used algorithms
                "VI.3. What has been released?": "P171107",  # released items
                "VI.4. What needs to be done for running the tool?": "P171105",  # tool running requirements
                "VI.5. What type of documentation has been provided alongside the tool?": "P171106",  # tool documentation type
                "VI.6. What type of dependencies does the tool have?": "P171110",  # tool dependencies
                "VI.7. How is the tool released?": "P171109",  # tool release method
                "VI.8. What license has been used?": "P171108",  # tool license
            },
            "evaluation": {
                "VII.1. What metrics are used to evaluate the approach(es)?": "P41532",  # evaluation metrics
                "VII.2. What is the validation procedure?": "P171096",  # validation procedure
                "VII.3. What baseline do you compare against?": "P171097",  # baseline comparison
                "VII.4. Please provide more details about the baseline you compare against": "P171098",  # baseline comparison details
            },
        }

        if field_name not in question_to_property_mappings:
            return

        property_mappings = question_to_property_mappings[field_name]

        # Process each question and map to appropriate property
        for question in questions:
            question_text = question.get("question_text", "")

            # Find matching property for this question
            for question_pattern, property_id in property_mappings.items():
                if question_pattern.lower() in question_text.lower():
                    answer = self.extract_answer_from_question(question)

                    if answer and answer.strip():
                        # Create literal for the answer
                        literal_response = self.orkg.literals.add(label=answer.strip())

                        if literal_response.succeeded:
                            # Link the answer to the subtemplate property
                            self.orkg.statements.add(
                                subject_id=subtemplate_id,
                                predicate_id=property_id,
                                object_id=literal_response.content["id"],
                            )
                            print(
                                f"    ✅ Added property {property_id}: {answer[:50]}{'...' if len(answer) > 50 else ''}"
                            )
                    break

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
            # Create the main instance
            instance_response = self.orkg.resources.add(
                label=paper_title,
                classes=[self.target_class_id],
            )

            if not instance_response.succeeded:
                print(f"❌ Failed to create instance")
                return None

            instance_id = instance_response.content["id"]
            print(f"✅ Created instance: {instance_id}")

            # Materialize the main template
            try:
                tp = self.orkg.templates
                tp.materialize_template(self.template_id)
                print("✅ Materialized main template")
            except Exception as e:
                print(f"⚠️ Could not materialize main template: {e}")

            # Process each template field
            for field_name in self.field_mappings.keys():
                print(f"\n🔍 Processing: {field_name}")

                # Extract data from JSON
                field_data = self.extract_field_data(json_data, field_name)

                # Check if this field has a subtemplate
                field_config = self.field_mappings[field_name]

                if "template_id" in field_config:
                    # Handle subtemplate fields
                    print(f"  📋 Creating subtemplate for {field_name}")
                    subtemplate_id = self.create_subtemplate_instance(
                        field_name, json_data, paper_title
                    )

                    if subtemplate_id:
                        # Link the subtemplate instance to the main instance
                        predicate_id = field_config["predicate"]

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
                    # Skip if field data is empty or only whitespace
                    if not field_data or not field_data.strip():
                        print(f"  ⚠️ No data found - skipping field")
                        continue

                    print(
                        f"  📊 Data: {field_data[:100]}{'...' if len(field_data) > 100 else ''}"
                    )

                    # Create literal with just the answer data
                    literal_id = self.create_literal_for_field(field_data)

                    if literal_id:
                        # Link the literal to the instance using the correct predicate
                        predicate_id = field_config["predicate"]

                        link_stmt = self.orkg.statements.add(
                            subject_id=instance_id,
                            predicate_id=predicate_id,
                            object_id=literal_id,
                        )

                        if link_stmt.succeeded:
                            print(
                                f"  ✅ Linked literal to instance with predicate {predicate_id}"
                            )
                        else:
                            print(f"  ⚠️ Failed to link literal to instance")
                    else:
                        print(f"  ⚠️ Failed to create literal - skipping field")

            print(f"\n✅ Instance created successfully!")
            print(f"Instance URL: https://incubating.orkg.org/resource/{instance_id}")
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
        print(f"🌐 View at: https://incubating.orkg.org/resource/{instance_id}")
    else:
        print(f"\n❌ Failed to create instance")


if __name__ == "__main__":
    main()
