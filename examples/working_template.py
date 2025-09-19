import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.orkg_connection import ORKGConnection

orkg = ORKGConnection()

# Create resources that actually work
paper_class = orkg.create_or_find_class("NLP Paper")
template_resource = orkg.create_resource("NLP Template", classes=[])

# Create predicates
predicates = {}
for pred in ["has title", "has author", "uses method"]:
    predicates[pred] = orkg.create_or_find_predicate(pred)

# Link template to predicates using existing predicate
for pred_id in predicates.values():
    orkg.add_statement(template_resource, "P6004", pred_id)  # has property

# Create example instance
instance = orkg.create_resource("Example Paper", classes=[paper_class])

# Add sample data
data = {
    "has title": "NLP for Requirements",
    "has author": "Research Team",
    "uses method": "Machine Learning",
}

for pred_label, value in data.items():
    literal = orkg.create_literal(value)
    orkg.add_statement(instance, predicates[pred_label], literal)

print(f"Template Resource: {template_resource}")
print(f"Instance: {instance}")
print(f"Instance URL: https://incubating.orkg.org/resource/{instance}")
