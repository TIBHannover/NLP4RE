"""
ORKG Connection and Basic Operations Module
"""

from orkg import ORKG
from .config import ORKG_HOST, ORKG_USERNAME, ORKG_PASSWORD
import uuid


class ORKGConnection:
    """Handles connection and basic operations with ORKG"""

    def __init__(self):
        """Initialize connection to ORKG"""
        self.orkg = ORKG(host=ORKG_HOST, creds=(ORKG_USERNAME, ORKG_PASSWORD))
        print("Successfully connected to ORKG.")

    def generate_unique_id(self, prefix="R"):
        """Generate a unique ID for ORKG resources"""
        return f"{prefix}{uuid.uuid4().hex[:10]}"

    def create_or_find_class(self, label, custom_id=None):
        """
        Create or find a class in ORKG with optional custom ID

        Args:
            label (str): The label for the class
            custom_id (str, optional): Custom ID to use when creating the class

        Returns:
            str: The ID of the class
        """
        # First, try to find existing class
        find_class = self.orkg.classes.get_all(q=label, exact=True).content
        if find_class["content"]:
            return find_class["content"][0]["id"]

        # Create new class with custom ID if provided
        if custom_id:
            resp = self.orkg.classes.add(label=label, id=custom_id)
            if resp.succeeded:
                return custom_id
        else:
            resp = self.orkg.classes.add(label=label)

        if not resp.succeeded:
            raise RuntimeError(
                f"Class '{label}' creation failed: {resp.status_code} {resp.content}"
            )

        # If we used a custom ID and it succeeded, return it
        if custom_id:
            return custom_id

        # Otherwise, find the newly created class
        find_new_class = self.orkg.classes.get_all(q=label, exact=True).content
        if find_new_class["content"]:
            return find_new_class["content"][0]["id"]

        # Fallback: get the most recently created class with this label
        all_classes = self.orkg.classes.get_all(q=label).content["content"]
        all_classes.sort(key=lambda x: x["created_at"], reverse=True)
        return all_classes[0]["id"]

    def create_or_find_predicate(self, label, custom_id=None):
        """
        Create or find a predicate in ORKG with optional custom ID

        Args:
            label (str): The label for the predicate
            custom_id (str, optional): Custom ID to use when creating the predicate

        Returns:
            str: The ID of the predicate
        """
        # First, try to find existing predicate
        find_predicate = self.orkg.predicates.get(q=label, exact=True).content
        if find_predicate["content"]:
            return find_predicate["content"][0]["id"]

        # Create new predicate with custom ID if provided
        if custom_id:
            resp = self.orkg.predicates.add(label=label, id=custom_id)
            if resp.succeeded:
                return custom_id
        else:
            resp = self.orkg.predicates.add(label=label)

        if not resp.succeeded:
            raise RuntimeError(
                f"Predicate '{label}' creation failed: {resp.status_code} {resp.content}"
            )

        # If we used a custom ID and it succeeded, return it
        if custom_id:
            return custom_id

        # Otherwise, find the newly created predicate
        predicates = self.orkg.predicates.get(q=label).content["content"]
        predicates.sort(key=lambda x: x["created_at"], reverse=True)
        return predicates[0]["id"]

    def create_resource(self, label, classes=None, custom_id=None):
        """
        Create a resource in ORKG with optional custom ID

        Args:
            label (str): The label for the resource
            classes (list, optional): List of class IDs to assign to the resource
            custom_id (str, optional): Custom ID to use when creating the resource

        Returns:
            str: The ID of the created resource
        """
        classes = classes or []

        if custom_id:
            resp = self.orkg.resources.add(label=label, classes=classes, id=custom_id)
            if resp.succeeded:
                return custom_id
        else:
            resp = self.orkg.resources.add(label=label, classes=classes)

        if not resp.succeeded:
            raise RuntimeError(
                f"Resource '{label}' creation failed: {resp.status_code} {resp.content}"
            )

        # If we used a custom ID and it succeeded, return it
        if custom_id:
            return custom_id

        # Otherwise, find the newly created resource
        try:
            resource = self.orkg.resources.get(q=label, exact=True).content["content"][
                0
            ]
            return resource["id"]
        except (IndexError, KeyError):
            # Fallback: get the most recently created resource with this label
            resources = self.orkg.resources.get(q=label).content["content"]
            resources.sort(key=lambda x: x["created_at"], reverse=True)
            return resources[0]["id"]

    def create_literal(self, label, datatype="xsd:string", custom_id=None):
        """
        Create a literal in ORKG with optional custom ID

        Args:
            label (str): The label for the literal
            datatype (str): The datatype of the literal
            custom_id (str, optional): Custom ID to use when creating the literal

        Returns:
            str: The ID of the created literal
        """
        # First, try to find existing literal
        existing = self.orkg.literals.get_all(q=label, exact=True).content
        if existing["content"]:
            return existing["content"][0]["id"]

        # Note: ORKG literals API doesn't support custom IDs
        resp = self.orkg.literals.add(label=label, datatype=datatype)

        if not resp.succeeded:
            raise RuntimeError(
                f"Literal '{label}' creation failed: {resp.status_code} {resp.content}"
            )

        # Find the newly created literal
        new_literal = self.orkg.literals.get_all(q=label, exact=True).content
        return new_literal["content"][0]["id"]

    def add_statement(self, subject_id, predicate_id, object_id):
        """Add a statement to ORKG"""
        return self.orkg.statements.add(
            subject_id=subject_id, predicate_id=predicate_id, object_id=object_id
        )
