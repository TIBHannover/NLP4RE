predicates = {
    "P181002": {
        "label": "RE task",
        "cardinality": "one to one",
        "description": "What requirements engineering task is your study addressing?",
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
            },
            "P181005": {
                "label": "NLP task input",
                "cardinality": "one to many",
                "description": "What is the input of your natural language processing task?",
            },
            "P181006": {
                "label": "NLP task output type",
                "cardinality": "one to one",
                "description": "What is the output of your natural language processing task?",
            },
        },
    },
    "P181011": {
        "label": "NLP dataset",
        "cardinality": "one to one",
        "description": "What natural language processing dataset is your study uing?",
        "subtemplate_id": "R1544216",
        "class_id": "C121010",
        "subtemplate_properties": {
            "P181015": {
                "label": "NLP data item",
                "cardinality": "one to one",
                "description": "How many data items do you process? Please report the numerical information and details about all the data that is used in your evaluation.",
            },
            "P181016": {
                "label": "NLP data prodcution time",
                "cardinality": "one to one",
                "description": "In which year or interval of year were the data produced?",
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
                    },
                    "P181019": {
                        "label": "Number of data sources",
                        "cardinality": "one to one",
                        "description": "From how many different sources your data comes from?",
                    },
                    "P181020": {
                        "label": "NLP data source domain",
                        "cardinality": "one to many",
                        "description": "Please list which domains your data belongs to (e.g., automotive, satellite,entertainment, information systems).",
                    },
                },
            },
            "P181021": {
                "label": "NLP data abstraction level",
                "cardinality": "one to many",
                "description": "What is the level of abstraction of the data (not limited to requirements)?",
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
                    },
                    "P181024": {
                        "label": "Rigor of data format",
                        "cardinality": "one to many",
                        "description": "How rigorous is the data format?",
                    },
                    "P181025": {
                        "label": "Natural language",
                        "cardinality": "one to one",
                        "description": "What is the natural language of the data (if applicable)?",
                    },
                },
            },
            "license": {
                "label": "License",
                "cardinality": "one to one",
                "description": "What license has been used?",
                "subtemplate_id": "R1544265",
                "class_id": "C121018",
                "subtemplate_properties": {
                    "P181026": {
                        "label": "Public availability",
                        "cardinality": "one to one",
                        "description": "Is the dataset publicly available?",
                    },
                    "P181027": {
                        "label": "License type",
                        "cardinality": "one to one",
                        "description": "What is the type of the license?",
                    },
                },
            },
            "P181028": {
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
                    },
                    "P1003": {
                        "label": "URL",
                        "cardinality": "one to one",
                        "description": "Provide a URL to the dataset, if available, or to the original paper that proposed the dataset",
                    },
                },
            },
        },
    },
    "P181031": {
        "label": "Annotation process",
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
                        "description": "How many annotators have been involved in your annotation process?",
                    },
                    "P181033": {
                        "label": "Annotator assignment",
                        "cardinality": "one to many",
                        "description": "How are the entries annotated assigned to the annotators?",
                    },
                    "P181034": {
                        "label": "Level of application domain experience",
                        "cardinality": "one to many",
                        "description": "What is the level of application domain experience of the annotators?",
                    },
                    "P181035": {
                        "label": "Annotator identity",
                        "cardinality": "one to many",
                        "description": "Who are the annotators?",
                    },
                },
            },
            "P181036": {
                "label": "Annotation scheme",
                "cardinality": "one to many",
                "description": "What is the annotation scheme used for your dataset?",
                "subtemplate_id": "R1544307",
                "class_id": "C121030",
                "subtemplate_properties": {
                    "P181037": {
                        "label": "Scheme establishement",
                        "cardinality": "one to many",
                        "description": "How was the annotation scheme established among the annotators?",
                    },
                    "P181038": {
                        "label": "Guideline availability",
                        "cardinality": "one to many",
                        "description": "Did you make the written guidelines public?",
                    },
                },
            },
            "P181039": {
                "label": "Shared material",
                "cardinality": "one to one",
                "description": "Did you share other information that could support the annotators other",
            },
            "P181040": {
                "label": "Fatigue mitigation technique",
                "cardinality": "one to one",
                "description": "Did you employ techniques to mitigate fatigue effects during the",
            },
            "P181041": {
                "label": "Annotator agreement",
                "cardinality": "one to one",
                "description": "What annotator agreement did you apply for your dataset?",
                "subtemplate_id": "R1544326",
                "class_id": "C121035",
                "subtemplate_properties": {
                    "P181042": {
                        "label": "Intercoder reliability metric",
                        "cardinality": "one to many",
                        "description": "What are the metrics used to measure intercoder reliability?",
                    },
                    "P181044": {
                        "label": "Conflict resolution",
                        "cardinality": "one to many",
                        "description": "How were conflicts resolved?",
                    },
                    "P181045": {
                        "label": "Measured agreement",
                        "cardinality": "one to one",
                        "description": "What is the measured agreement?",
                    },
                },
            },
        },
    },
    "P181046": {
        "label": "Implemented approach",
        "cardinality": "one to one",
        "description": "What approach did you implement for your study?",
        "subtemplate_id": "R1544363",
        "class_id": "C121038",
        "subtemplate_properties": {
            "P5043": {
                "label": "Approach type",
                "cardinality": "one to many",
                "description": "What is the type of the implemented approach?",
            },
            "P58069": {
                "label": "Algorithm used",
                "cardinality": "one to many",
                "description": "What algorithms are used in the implemented approach?",
            },
            "P181047": {
                "label": "Running requirement",
                "cardinality": "one to many",
                "description": "What needs to be done for running the implemented approach?",
            },
            "P41835": {
                "label": "Documentation",
                "cardinality": "one to many",
                "description": "What type of documentation has been provided alongside the implemented approach?",
            },
            "P181048": {
                "label": "Dependency",
                "cardinality": "one to many",
                "description": "What type of dependencies does the implemented approach have?",
            },
            "P181027": {
                "label": "License type",
                "cardinality": "one to one",
                "description": "What license has been used?",
            },
            "release": {
                "label": "Release",
                "cardinality": "one to one",
                "description": "How was the implemented approach released?",
                "subtemplate_id": "R1544401",
                "class_id": "C121044",
                "subtemplate_properties": {
                    "P181049": {
                        "label": "Release format",
                        "cardinality": "one to many",
                        "description": "What has been released?",
                    },
                    "P181029": {
                        "label": "Location type",
                        "cardinality": "one to many",
                        "description": "How is the tool released?",
                    },
                    "P1003": {
                        "label": "URI",
                        "cardinality": "one to one",
                        "description": "Where is the tool released?",
                    },
                },
            },
        },
    },
    "HAS_EVALUATION": {
        "label": "Evaluation",
        "cardinality": "one to one",
        "description": "What evaluation did you apply for your study?",
        "subtemplate_id": "R1544421",
        "class_id": "C121047",
        "subtemplate_properties": {
            "P110006": {
                "label": "Evaluation metric",
                "cardinality": "one to many",
                "description": "What metrics are used to evaluate the implemented approach(?",
            },
            "P181050": {
                "label": "Validation procedure",
                "cardinality": "one to many",
                "description": "What is the validation procedure?",
            },
            "P181051": {
                "label": "Baseline comparison",
                "cardinality": "one to one",
                "description": "What is the baseline comparison applied in the evaluation of an implemented approach?",
                "subtemplate_id": "R1544450",
                "class_id": "C121050",
                "subtemplate_properties": {
                    "P181052": {
                        "label": "Baseline comparison type",
                        "cardinality": "one to many",
                        "description": "What baseline do you compare against?",
                    },
                    "P181053": {
                        "label": "Baseline comparison details",
                        "cardinality": "one to one",
                        "description": "Please provide more details about the baseline you compare against, if any.",
                    },
                },
            },
        },
    },
}
