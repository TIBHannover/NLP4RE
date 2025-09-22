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

        self.template_id = "R1544125"
        self.target_class_id = "C121001"

        # Load predefined resource mappings from Question Answer - ORKG Resource Mappring.txt
        self.resource_mappings = self.load_resource_mappings()

        # Field mappings based on NLP4RE ID Card template structure
        self.predicates = {
            "P181002": {
                "label": "RE task",
                "cardinality": "one to one",
                "description": "What requirements engineering task is your study addressing?",
                "question_mapping": "I.1",
                "resource_mapping_key": "RE task",
            },
            "P181003": {
                "label": "NLP task",
                "cardinality": "one to one",
                "description": "What natural language processing task is your study tackling?",
                "subtemplate_id": "R1544138",
                "class_id": "C121004",
                "subtemplate_properties": {
                    "P181004": {
                        "label": "NLP task type",
                        "cardinality": "one to many",
                        "description": "What type of natural language processing task is your study tackling?",
                        "question_mapping": "II.1",
                        "resource_mapping_key": "NLP task type",
                    },
                    "P181005": {
                        "label": "NLP task input",
                        "cardinality": "one to many",
                        "description": "What is the input of your natural language processing task?",
                        "question_mapping": "III.1",
                        "resource_mapping_key": "NLP task input",
                    },
                    "P181006": {
                        "label": "NLP task output type",
                        "cardinality": "one to many",
                        "description": "What is the output of your natural language processing task?",
                        "question_mapping": [
                            "III.2",
                            "III.4",
                            "III.6",
                            "III.8",
                            "III.9",
                        ],
                        "resource_mapping_key": "NLP task output type",
                    },
                    "P181007": {
                        "label": "NLP task output classification label",
                        "cardinality": "one to one",
                        "description": "What are the labels that can be assigned?",
                        "question_mapping": "III.3",
                        "resource_mapping_key": "NLP task output classification label",
                    },
                    "P181008": {
                        "label": "NLP task output extracted element",
                        "cardinality": "one to one",
                        "description": "What is the type of the extracted elements?",
                        "question_mapping": "III.5",
                        "resource_mapping_key": "NLP task output extracted element",
                    },
                    "P181009": {
                        "label": "NLP task output translation mapping cardinality",
                        "cardinality": "one to one",
                        "description": "What is the translation mapping cardinality between initial input and final output?",
                        "question_mapping": "III.7",
                        "resource_mapping_key": "NLP task output translation mapping cardinality",
                    },
                },
            },
            "P181011": {
                "label": "NLP dataset",
                "cardinality": "one to one",
                "description": "What natural language processing dataset is your study using?",
                "subtemplate_id": "R1544216",
                "class_id": "C121010",
                "subtemplate_properties": {
                    "P181015": {
                        "label": "NLP data item",
                        "cardinality": "one to one",
                        "description": "How many data items do you process?",
                        "question_mapping": "IV.1",
                        "resource_mapping_key": "NLP data item",
                    },
                    "P181016": {
                        "label": "NLP data production time",
                        "cardinality": "one to one",
                        "description": "In which year or interval of year were the data produced?",
                        "question_mapping": "IV.2",
                        "resource_mapping_key": "NLP data prodcution time",
                    },
                    "P181017": {
                        "label": "NLP data source",
                        "cardinality": "one to one",
                        "description": "What is the source of the data?",
                        "subtemplate_id": "R1544223",
                        "class_id": "C121011",
                        "subtemplate_properties": {
                            "P181018": {
                                "label": "NLP data source type",
                                "cardinality": "one to one",
                                "description": "What is the source type of the data?",
                                "question_mapping": "IV.3",
                                "resource_mapping_key": "NLP data source type",
                            },
                            "P181019": {
                                "label": "Number of data sources",
                                "cardinality": "one to one",
                                "description": "From how many different sources your data comes from?",
                                "question_mapping": "IV.9",
                                "resource_mapping_key": "Number of data sources",
                            },
                            "P181020": {
                                "label": "NLP data source domain",
                                "cardinality": "one to many",
                                "description": "Please list which domains your data belongs to?",
                                "question_mapping": "IV.8",
                                "resource_mapping_key": "NLP data source domain",
                                "comma_separated": True,
                            },
                        },
                    },
                    "P181021": {
                        "label": "NLP data abstraction level",
                        "cardinality": "one to many",
                        "description": "What is the level of abstraction of the data?",
                        "question_mapping": "IV.4",
                        "resource_mapping_key": "NLP data abstraction level",
                    },
                    "P181022": {
                        "label": "NLP data type",
                        "cardinality": "one to one",
                        "description": "What is the type of the data?",
                        "subtemplate_id": "R1544245",
                        "class_id": "C121015",
                        "subtemplate_properties": {
                            "P181023": {
                                "label": "NLP data format",
                                "cardinality": "one to one",
                                "description": "What is the format of the data?",
                                "question_mapping": "IV.5",
                                "resource_mapping_key": "NLP data format",
                            },
                            "P181024": {
                                "label": "Rigor of data format",
                                "cardinality": "one to many",
                                "description": "How rigorous is the data format?",
                                "question_mapping": "IV.6",
                                "resource_mapping_key": "Rigor of data format",
                            },
                            "P181025": {
                                "label": "Natural language",
                                "cardinality": "one to one",
                                "description": "What is the natural language of the data?",
                                "question_mapping": "IV.7",
                                "resource_mapping_key": "Natural language",
                            },
                        },
                    },
                    "P181026": {
                        "label": "License",
                        "cardinality": "one to one",
                        "description": "What license information applies?",
                        "subtemplate_id": "R1544265",
                        "class_id": "C121018",
                        "subtemplate_properties": {
                            "P181027": {
                                "label": "Public availability",
                                "cardinality": "one to one",
                                "description": "Is the dataset publicly available?",
                                "question_mapping": "IV.10",
                                "resource_mapping_key": "Public availability",
                            },
                            "P181028": {
                                "label": "License type",
                                "cardinality": "one to one",
                                "description": "What is the type of the license?",
                                "question_mapping": "IV.11",
                                "resource_mapping_key": "License type",
                            },
                        },
                    },
                    "P181029": {
                        "label": "Dataset location",
                        "cardinality": "one to one",
                        "description": "Where is the dataset stored?",
                        "subtemplate_id": "R1544278",
                        "class_id": "C121022",
                        "subtemplate_properties": {
                            "P181030": {
                                "label": "Location type",
                                "cardinality": "one to many",
                                "description": "Where is the dataset stored?",
                                "question_mapping": "IV.12",
                                "resource_mapping_key": "Location type",
                            },
                            "P1003": {
                                "label": "URL",
                                "cardinality": "one to one",
                                "description": "Provide a URL to the dataset",
                                "question_mapping": "IV.13",
                                "resource_mapping_key": "url",
                            },
                        },
                    },
                },
            },
            "P181031": {
                "label": "Annotation Process",
                "cardinality": "one to one",
                "description": "What annotation process did you use for your dataset?",
                "subtemplate_id": "R1544287",
                "class_id": "C121025",
                "subtemplate_properties": {
                    "P181032": {
                        "label": "Annotator",
                        "cardinality": "one to one",
                        "description": "Who are the annotators of your dataset?",
                        "subtemplate_id": "R1544290",
                        "class_id": "C121026",
                        "subtemplate_properties": {
                            "P59120": {
                                "label": "Number of annotators",
                                "cardinality": "one to one",
                                "description": "How many annotators have been involved?",
                                "question_mapping": "V.1",
                                "resource_mapping_key": "Number of annotators",
                            },
                            "P181033": {
                                "label": "Annotator assignment",
                                "cardinality": "one to many",
                                "description": "How are the entries annotated?",
                                "question_mapping": "V.2",
                                "resource_mapping_key": "Annotator assignment",
                            },
                            "P181034": {
                                "label": "Level of application domain experience",
                                "cardinality": "one to many",
                                "description": "What is the level of application domain experience?",
                                "question_mapping": "V.3",
                                "resource_mapping_key": "Level of application domain experience",
                            },
                            "P181035": {
                                "label": "Annotator identity",
                                "cardinality": "one to many",
                                "description": "Who are the annotators?",
                                "question_mapping": "V.4",
                                "resource_mapping_key": "Annotator identity",
                            },
                        },
                    },
                    "P181036": {
                        "label": "Annotation scheme",
                        "cardinality": "one to many",
                        "description": "What is the annotation scheme used?",
                        "subtemplate_id": "R1544307",
                        "class_id": "C121030",
                        "subtemplate_properties": {
                            "P181037": {
                                "label": "Scheme establishment",
                                "cardinality": "one to many",
                                "description": "How was the annotation scheme established?",
                                "question_mapping": "V.5",
                                "resource_mapping_key": "Scheme establishement",
                            },
                            "P181038": {
                                "label": "Guideline availability",
                                "cardinality": "one to many",
                                "description": "Did you make the written guidelines public?",
                                "question_mapping": "V.6",
                                "resource_mapping_key": "Guideline availability",
                            },
                        },
                    },
                    "P181039": {
                        "label": "Shared material",
                        "cardinality": "one to one",
                        "description": "Did you share other information to support annotators?",
                        "question_mapping": "V.7",
                        "resource_mapping_key": "Shared material",
                    },
                    "P181040": {
                        "label": "Fatigue mitigation technique",
                        "cardinality": "one to one",
                        "description": "Did you employ techniques to mitigate fatigue effects?",
                        "question_mapping": "V.8",
                        "resource_mapping_key": "Fatigue mitigation technique",
                    },
                    "P181041": {
                        "label": "Annotator agreement",
                        "cardinality": "one to one",
                        "description": "What annotator agreement did you apply?",
                        "subtemplate_id": "R1544326",
                        "class_id": "C121035",
                        "subtemplate_properties": {
                            "P181042": {
                                "label": "Intercoder reliability metric",
                                "cardinality": "one to many",
                                "description": "What are the metrics used to measure intercoder reliability?",
                                "question_mapping": "V.9",
                                "resource_mapping_key": "Intercoder reliability metric",
                            },
                            "P181044": {
                                "label": "Conflict resolution",
                                "cardinality": "one to many",
                                "description": "How were conflicts resolved?",
                                "question_mapping": "V.10",
                                "resource_mapping_key": "Conflict resolution",
                            },
                            "P181045": {
                                "label": "Measured agreement",
                                "cardinality": "one to one",
                                "description": "What is the measured agreement?",
                                "question_mapping": "V.11",
                                "resource_mapping_key": "Measured agreement",
                            },
                        },
                    },
                },
            },
            "P181046": {
                "label": "Implemented approach",
                "cardinality": "one to one",
                "description": "What approach did you implement?",
                "subtemplate_id": "R1544363",
                "class_id": "C121038",
                "subtemplate_properties": {
                    "P5043": {
                        "label": "Approach type",
                        "cardinality": "one to many",
                        "description": "What is the type of proposed solution?",
                        "question_mapping": "VI.1",
                        "resource_mapping_key": "Approach type",
                    },
                    "P58069": {
                        "label": "Algorithm used",
                        "cardinality": "one to many",
                        "description": "What algorithms are used in the tool?",
                        "question_mapping": "VI.2",
                        "resource_mapping_key": "Algorithm used",
                        "comma_separated": True,
                    },
                    "P181047": {
                        "label": "Running requirements",
                        "cardinality": "one to many",
                        "description": "What needs to be done for running the tool?",
                        "question_mapping": "VI.4",
                        "resource_mapping_key": "Running requirements",
                    },
                    "P41835": {
                        "label": "Documentation",
                        "cardinality": "one to many",
                        "description": "What type of documentation has been provided?",
                        "question_mapping": "VI.5",
                        "resource_mapping_key": "Documentation",
                    },
                    "P181048": {
                        "label": "Dependency",
                        "cardinality": "one to many",
                        "description": "What type of dependencies does the tool have?",
                        "question_mapping": "VI.6",
                        "resource_mapping_key": "Dependency",
                    },
                    "P181049": {
                        "label": "License type",
                        "cardinality": "one to one",
                        "description": "What license has been used?",
                        "question_mapping": "VI.8",
                        "resource_mapping_key": "license type",
                    },
                    "P181050": {
                        "label": "Release",
                        "cardinality": "one to one",
                        "description": "How was the tool released?",
                        "subtemplate_id": "R1544401",
                        "class_id": "C121044",
                        "subtemplate_properties": {
                            "P181051": {
                                "label": "Release format",
                                "cardinality": "one to many",
                                "description": "What has been released?",
                                "question_mapping": "VI.3",
                                "resource_mapping_key": "Release format",
                            },
                            "P181052": {
                                "label": "Location type",
                                "cardinality": "one to many",
                                "description": "How is the tool released?",
                                "question_mapping": "VI.7",
                                "resource_mapping_key": "Location type",
                            },
                            "P1003": {
                                "label": "URL",
                                "cardinality": "one to one",
                                "description": "Where is the tool released?",
                                "question_mapping": "VI.9",
                                "resource_mapping_key": "url",
                            },
                        },
                    },
                },
            },
            "P181053": {
                "label": "Evaluation",
                "cardinality": "one to one",
                "description": "What evaluation did you apply?",
                "subtemplate_id": "R1544421",
                "class_id": "C121047",
                "subtemplate_properties": {
                    "P110006": {
                        "label": "Evaluation metric",
                        "cardinality": "one to many",
                        "description": "What metrics are used to evaluate the approach?",
                        "question_mapping": "VII.1",
                        "resource_mapping_key": "Evaluation metric",
                        "comma_separated": True,
                    },
                    "P181054": {
                        "label": "Validation procedure",
                        "cardinality": "one to many",
                        "description": "What is the validation procedure?",
                        "question_mapping": "VII.2",
                        "resource_mapping_key": "Validation procedure",
                    },
                    "P181055": {
                        "label": "Baseline comparison",
                        "cardinality": "one to one",
                        "description": "What is the baseline comparison?",
                        "subtemplate_id": "R1544450",
                        "class_id": "C121050",
                        "subtemplate_properties": {
                            "P181056": {
                                "label": "Baseline comparison type",
                                "cardinality": "one to many",
                                "description": "What baseline do you compare against?",
                                "question_mapping": "VII.3",
                                "resource_mapping_key": "Baseline comparsion type",
                            },
                            "P181057": {
                                "label": "Baseline comparison details",
                                "cardinality": "one to one",
                                "description": "Please provide more details about the baseline?",
                                "question_mapping": "VII.4",
                                "resource_mapping_key": "Baseline comparison details",
                            },
                        },
                    },
                },
            },
        }
        # Question to predicate mappings based on NLP4RE ID Card structure
        self.question_mappings = self.build_question_mappings()

    def load_resource_mappings(self) -> Dict[str, Dict[str, str]]:
        """Load resource mappings from the Question Answer - ORKG Resource Mappring.txt file"""
        resource_mappings = {
            "RE task": {
                "Requirements retrieval": "R1544135",
                "Requirements tracing": "R1544133",
                "Information extraction from legal documents": "R1544136",
                "Requirements defect detection": "R1544134",
                "Requirements classification": "R1544130",
                "Model generation": "R1544132",
                "App review analysis": "R1544129",
                "Dependency and relation extraction": "R1544131",
                "Test generation": "R1544128",
                "Information extraction from requirements": "R1544127",
            },
            "NLP task type": {
                "Information extraction": "R1544150",
                "Information retrieval": "R1544149",
                "Classification": "R1544148",
                "Translation": "R1544147",
            },
            "NLP task input": {
                "Words": "R1544156",
                "Structured/tabular text": "R1544155",
                "Phrases": "R1544154",
                "Document": "R1544153",
                "Paragraphs": "R1544151",
                "Sentences": "R1544152",
            },
            "NLP task output type": {
                "Text": "R1544175",
                "Binary-multi label": "R1544174",
                "Multi class-single label": "R1544171",
                "Multi class-multi label": "R1544169",
                "Phrases": "R1544167",
                "Sentences": "R1544173",
                "Words": "R1544170",
                "Table": "R1544172",
                "Graphical diagram": "R1544168",
                "Document": "R1544166",
                "Binary-single label": "R1544161",
                "Executable model": "R1544165",
                "Paragraphs": "R1544164",
                "Test cases": "R1544163",
            },
            "NLP task output translation mapping cardinality": {
                "Not reported": "R1544465",
                "Many to Many": "R1544187",
                "Many to 1": "R1544186",
                "1 to many": "R1544185",
                "1 to 1": "R1544184",
            },
            "NLP data source type": {
                "Textbook examples or cases": "R1544232",
                "Student projects": "R1544231",
                "Industrial project, publicly available data": "R1544230",
                "User generated content": "R1544229",
                "Toy Requirements": "R1544227",
                "Industrial project, proprietary data": "R1544228",
                "Legal/regulatory documents": "R1544226",
                "Community-based open source projects": "R1544225",
            },
            "NLP data source domain": {
                "Not reported": "R1544550",
            },
            "NLP data abstraction level": {
                "Module-level": "R1544243",
                "Code-level": "R1544242",
                "System-level": "R1544241",
                "Business-level": "R1544240",
                "Normative-level": "R1544239",
                "User-level": "R1544238",
            },
            "NLP data format": {
                "Legal text": "R1544255",
                "Messages in user forums": "R1544254",
                "Social media posts": "R1544256",
                "Bug/defect reports": "R1544253",
                "User reviews": "R1544252",
                "Use cases": "R1544251",
                "Graphical diagrams": "R1544247",
                "User stories": "R1544248",
                "Scenarios": "R1544250",
                '"Shall" requirements': "R1544249",
            },
            "Rigor of data format": {
                "Semantically-augmented natural language": "R1544261",
                "Restricted grammar based controlled natural language": "R1544260",
                "Template-based controlled natural language": "R1544259",
                "Unconstrained natural language": "R1544258",
            },
            "Public availability": {
                "Upon Request": "R1544270",
                "Partially": "R1544269",
                "No": "R1544268",
                "Fully": "R1544267",
            },
            "License type": {
                "Not reported": "R1544495",
                "No license": "R1544274",
                "License: Reuse for any purposes": "R1544276",
                "License: Modification only for non-commercial purposes": "R1544275",
                "License: Modification for any purposes": "R1544273",
                "License: Reuse only for non-commercial purposes": "R1544272",
            },
            "Location type": {
                "Not reported": "R1544497",
                "In a persistent platform with DOI": "R1544282",
                "In a repository": "R1544281",
                "On a private/corporate website": "R1544280",
            },
            "Annotator assignment": {
                "One annotator per entry (quality control, possibly on a sample)": "R1544296",
                "One annotator per entry (no quality control)": "R1544295",
                "Partly multiple annotators per entry, partly one annotator per entry": "R1544294",
                "Multiple annotators per entry": "R1544293",
            },
            "Level of application domain experience": {
                "None or unknown": "R1544298",
                "Domain expert": "R1544299",
                "Informed outsider": "R1544300",
            },
            "Annotator identity": {
                "The designers of the technique/tool": "R1544302",
                "People who have direct contact with the designers": "R1544304",
                "Independent annotators": "R1544303",
            },
            "Scheme establishement": {
                "Written guidelines with label definitions": "R1544312",
                "Oral agreement among the annotators": "R1544311",
                "Only via class labels": "R1544309",
                "Written guidelines with definitions and examples": "R1544310",
            },
            "Guideline availability": {
                "Not reported": "R1544508",
                "Yes, via a persistent URL": "R1544317",
                "Yes, via a non-persistent URL": "R1544316",
                "No, but are made available upon request": "R1544315",
                "No": "R1544314",
            },
            "Shared material": {
                "Entire document": "R1544321",
                "Surrounding context": "R1544320",
                "No": "R1544319",
            },
            "Fatigue mitigation technique": {
                "No": "R1544324",
                "Yes": "R1544323",
            },
            "Intercoder reliability metric": {
                "Not reported": "R1544513",
                "Krippendorf's Alpha": "R1544330",
                "Fleiss K": "R1544329",
                "Cohen's K": "R1544328",
            },
            "Conflict resolution": {
                "Disagreements were disregarded": "R1544338",
                "Not resolved": "R1544335",
                "Majority voting": "R1544336",
                "Resolution by independent expert (not an annotator)": "R1544337",
                "Resolution by authors": "R1544334",
                "Discussion among annotators": "R1544333",
            },
            "Approach type": {
                "Unsupervised DL": "R1544369",
                "Supervised ML": "R1544368",
                "Rule-based": "R1544366",
                "Unsupervised ML": "R1544367",
                "Supervised DL": "R1544365",
            },
            "Algorithm used": {
                "Not reported": "R1544560",
            },
            "Running requirements": {
                "Not reported": "R1544524",
                "Virtual machine / Docker container": "R1544383",
                "Reproduce the tool from the explanation in the paper": "R1544382",
                "Import and integrate into your own code": "R1544381",
                "Compile and run": "R1544380",
                "No installation is needed": "R1544379",
            },
            "Documentation": {
                "Not reported": "R1544527",
                "Wiki or dedicated website": "R1544391",
                "README file": "R1544390",
                "An academic paper": "R1544386",
                "No documentation": "R1544389",
                "Tutorial": "R1544388",
                "Ready-to-use examples": "R1544387",
                "Pseudocode /illustration in the paper": "R1544385",
            },
            "Dependency": {
                "Not reported": "R1544528",
                "Specific OS": "R1544395",
                "Specific hardware": "R1544398",
                "Proprietary libraries/software": "R1544396",
                "External knowledge bases": "R1544397",
                "Open source libraries / software": "R1544394",
                "None": "R1544393",
            },
            "Release format": {
                "Library/API": "R1544411",
                "Pre-trained model": "R1544409",
                "Source code": "R1544410",
                "Executable notebook": "R1544407",
                "Service on the web": "R1544408",
                "Tool - standalone": "R1544405",
                "No tool has been released": "R1544406",
            },
            "Evaluation metric": {
                "MAP": "R1544443",
                "F-Score": "R1544442",
                "NIST-METEOR-ROUGE - BLEU": "R1544441",
                "Accuracy": "R1544440",
                "LAG": "R1544439",
                "AUC": "R1544438",
                "WER (word error rate)": "R1544437",
                "Precision/Recall": "R1544436",
            },
            "Validation procedure": {
                "Cross-project validation": "R1544447",
                "Cross-validation": "R1544448",
                "Train-test split": "R1544445",
                "Entire dataset": "R1544446",
            },
            "Baseline comparsion type": {
                "Theoretical/conceptual": "R1544457",
                "None": "R1544454",
                "Existing tool or algorithm": "R1544455",
                "Reconstructed tool from other research": "R1544456",
                "Automated, but self-defined": "R1544453",
                "Human baseline": "R1544452",
            },
        }
        return resource_mappings

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

    def extract_answer_from_question(self, question_data: Dict) -> List[str]:
        """Extract the answer from a question data structure"""
        answers = []

        # Check if question has any meaningful content
        question_text = question_data.get("question_text", "").strip()
        if not question_text:
            return []

        # Extract direct text answers
        if question_data.get("answer"):
            answer = question_data["answer"].strip()
            if answer:
                answers.append(answer)

        # Extract selected answers from multiple choice
        if question_data.get("selected_answers"):
            for answer in question_data["selected_answers"]:
                if answer and answer.strip() and answer.strip() not in ["None"]:
                    # Split comma-separated answers
                    if "," in answer and len(answer.split(",")) > 1:
                        for sub_answer in answer.split(","):
                            sub_answer = sub_answer.strip()
                            if sub_answer and sub_answer not in answers:
                                answers.append(sub_answer)
                    else:
                        answers.append(answer.strip())

        # Extract from options details
        if question_data.get("options_details"):
            for option in question_data["options_details"]:
                if option.get("is_selected"):
                    # Add label if it exists and is not empty
                    if option.get("label") and option["label"].strip():
                        answer_to_add = option["label"].strip().lower()
                        if answer_to_add not in answers and answer_to_add not in [
                            "None"
                        ]:
                            answers.append(answer_to_add)

                    # Add field value if it exists and is meaningful
                    field_value = option.get("field_value", "")
                    if (
                        field_value
                        and field_value.strip()
                        and field_value not in ["Yes", "Off", "", "None"]
                    ):
                        if field_value.strip() not in answers:
                            answers.append(field_value.strip())

        # Extract text input value for "Other/Comments" fields
        if question_data.get("text_input_value"):
            text_input = question_data["text_input_value"].strip()
            if text_input and text_input not in ["", "None"]:
                answers.append(text_input)

        # Filter out empty answers and return
        filtered_answers = [ans for ans in answers if ans and ans.strip()]
        return filtered_answers

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
        self, answer: str, resource_mapping_key: str
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
                "other (e.g., models, trace links, diagrams, code comments)/comments",
            ]:
                # Just "Other/Comments" without specific text - use "Unknown"
                return self.create_new_resource_for_other(
                    "Unknown", resource_mapping_key
                )
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
            class_mappings = {
                "RE task": "C121003",
                "NLP task type": "C121005",
                "NLP task input": "C121006",
                "NLP task output type": "C121008",
                "NLP task output translation mapping cardinality": "C121009",
                "NLP data source type": "C121012",
                "NLP data source domain": "C121053",
                "NLP data abstraction level": "C121013",
                "NLP data format": "C121016",
                "Rigor of data format": "C121017",
                "Public availability": "C121019",
                "License type": "C121020",
                "Location type": "C121024",
                "Annotator assignment": "C121027",
                "Level of application domain experience": "C121028",
                "Annotator identity": "C121029",
                "Scheme establishement": "C121031",
                "Guideline availability": "C121032",
                "Shared material": "C121033",
                "Fatigue mitigation technique": "C121034",
                "Intercoder reliability metric": "C121036",
                "Conflict resolution": "C121037",
                "Approach type": "C121039",
                "Algorithm used": "C121040",
                "Running requirements": "C121041",
                "Documentation": "C121042",
                "Dependency": "C121043",
                "Release format": "C121046",
                "Evaluation metric": "C121048",
                "Validation procedure": "C121049",
                "Baseline comparsion type": "C121051",
            }

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
        self, answers: List[str], resource_mapping_key: str
    ) -> List[str]:
        """Create literals or map to resources based on the answers"""
        result_ids = []

        for answer in answers:
            # First try to map to existing resource
            resource_id = self.map_answer_to_resource(answer, resource_mapping_key)

            if resource_id:
                result_ids.append(resource_id)
                print(f"  ✅ Mapped '{answer}' to resource: {resource_id}")
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

        # Handle comma separation if specified
        if property_info.get("comma_separated", False):
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
                    return None
            else:
                instance_id = instance_response.content["id"]
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
