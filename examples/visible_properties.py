import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.orkg_connection import ORKGConnection

orkg = ORKGConnection()

# Create class and template
paper_class = orkg.create_or_find_class("Test Paper")
template = orkg.create_resource("Test Template", classes=["NodeShape"])
orkg.add_statement(template, "sh:targetClass", paper_class)

# Create predicates and property shapes
predicates = {}
properties = ["has title", "has author", "has year"]

for prop in properties:
    # Create predicate
    pred_id = orkg.create_or_find_predicate(prop)
    predicates[prop] = pred_id

    # Create property shape
    shape_id = orkg.create_resource(f"Shape: {prop}", classes=["PropertyShape"])

    # Link template -> property shape
    orkg.add_statement(template, "sh:property", shape_id)

    # Link property shape -> predicate
    orkg.add_statement(shape_id, "sh:path", pred_id)

    # Set datatype
    if "year" in prop:
        orkg.add_statement(shape_id, "sh:datatype", "xsd:integer")
    else:
        orkg.add_statement(shape_id, "sh:datatype", "xsd:string")

# Create instances with data
for i in range(3):
    instance = orkg.create_resource(f"Paper {i+1}", classes=[paper_class])

    # Add data for each property
    title_lit = orkg.create_literal(f"Research Paper Title {i+1}")
    author_lit = orkg.create_literal(f"Author {i+1}")
    year_lit = orkg.create_literal(f"202{i}", datatype="xsd:integer")

    orkg.add_statement(instance, predicates["has title"], title_lit)
    orkg.add_statement(instance, predicates["has author"], author_lit)
    orkg.add_statement(instance, predicates["has year"], year_lit)

print(f"Template: {template}")
print(f"URL: https://incubating.orkg.org/template/{template}")
print("Created 3 instances with all properties")
