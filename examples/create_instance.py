import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.orkg_connection import ORKGConnection

orkg = ORKGConnection()

# Get existing resources
paper_class = orkg.create_or_find_class("Research Paper")
title_pred = orkg.create_or_find_predicate("has title")
author_pred = orkg.create_or_find_predicate("has author")

# Create instance
instance = orkg.create_resource("My Paper", classes=[paper_class])

# Add data
title_literal = orkg.create_literal("Understanding ORKG")
author_literal = orkg.create_literal("John Doe")

orkg.add_statement(instance, title_pred, title_literal)
orkg.add_statement(instance, author_pred, author_literal)

print(f"Instance: {instance}")
print(f"URL: https://incubating.orkg.org/resource/{instance}")
