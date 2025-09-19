import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.orkg_connection import ORKGConnection

orkg = ORKGConnection()

# Create class and template
paper_class = orkg.create_or_find_class("Research Paper")
template = orkg.create_resource("Paper Template", classes=["NodeShape"])
orkg.add_statement(template, "sh:targetClass", paper_class)

# Create properties
title_pred = orkg.create_or_find_predicate("has title")
author_pred = orkg.create_or_find_predicate("has author")

# Create property shapes
title_shape = orkg.create_resource("Title Shape", classes=["PropertyShape"])
orkg.add_statement(template, "sh:property", title_shape)
orkg.add_statement(title_shape, "sh:path", title_pred)
orkg.add_statement(title_shape, "sh:datatype", "xsd:string")

author_shape = orkg.create_resource("Author Shape", classes=["PropertyShape"])
orkg.add_statement(template, "sh:property", author_shape)
orkg.add_statement(author_shape, "sh:path", author_pred)
orkg.add_statement(author_shape, "sh:datatype", "xsd:string")

# Create instances
instance1 = orkg.create_resource("Paper 1", classes=[paper_class])
title1 = orkg.create_literal("Machine Learning in NLP")
author1 = orkg.create_literal("John Smith")
orkg.add_statement(instance1, title_pred, title1)
orkg.add_statement(instance1, author_pred, author1)

instance2 = orkg.create_resource("Paper 2", classes=[paper_class])
title2 = orkg.create_literal("Deep Learning Applications")
author2 = orkg.create_literal("Jane Doe")
orkg.add_statement(instance2, title_pred, title2)
orkg.add_statement(instance2, author_pred, author2)

print(f"Template: {template}")
print(f"Template URL: https://incubating.orkg.org/template/{template}")
print(f"Instance 1: https://incubating.orkg.org/resource/{instance1}")
print(f"Instance 2: https://incubating.orkg.org/resource/{instance2}")
