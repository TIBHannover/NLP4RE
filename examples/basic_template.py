import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.orkg_connection import ORKGConnection

orkg = ORKGConnection()

# Create class
paper_class = orkg.create_or_find_class("Research Paper")

# Create predicates
title_pred = orkg.create_or_find_predicate("has title")
author_pred = orkg.create_or_find_predicate("has author")

# Create SHACL template
template = orkg.create_resource("Simple Template", classes=["NodeShape"])
orkg.add_statement(template, "sh:targetClass", paper_class)

# Create property shapes
title_shape = orkg.create_resource("Title Shape", classes=["PropertyShape"])
orkg.add_statement(template, "sh:property", title_shape)
orkg.add_statement(title_shape, "sh:path", title_pred)
orkg.add_statement(title_shape, "sh:datatype", "xsd:string")

author_shape = orkg.create_resource("Author Shape", classes=["PropertyShape"])
orkg.add_statement(template, "sh:property", author_shape)
orkg.add_statement(author_shape, "sh:path", author_pred)
orkg.add_statement(author_shape, "sh:datatype", "xsd:string")

print(f"Template: {template}")
print(f"URL: https://incubating.orkg.org/template/{template}")
