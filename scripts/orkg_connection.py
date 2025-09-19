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

    def _extract_list(self, response_content):
        """Return a list of items from an ORKG client response content.

        Depending on the client and endpoint, the wrapped response `.content` can
        be either a list of items or a dict with a `content` list inside. This
        helper normalizes both shapes to a list.
        """
        if isinstance(response_content, list):
            return response_content
        if isinstance(response_content, dict) and "content" in response_content:
            inner = response_content.get("content")
            if isinstance(inner, list):
                return inner
        return []

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
        find_resp = self.orkg.classes.get_all(q=label, exact=True)
        existing = self._extract_list(find_resp.content)
        if existing:
            return existing[0]["id"]

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
        find_new_resp = self.orkg.classes.get_all(q=label, exact=True)
        new_list = self._extract_list(find_new_resp.content)
        if new_list:
            return new_list[0]["id"]

        # Fallback: get the most recently created class with this label
        all_resp = self.orkg.classes.get_all(q=label)
        all_classes = self._extract_list(all_resp.content)
        if all_classes:
            try:
                all_classes.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            except Exception:
                pass
            return all_classes[0]["id"]
        raise RuntimeError(f"Unable to find or create class '{label}'")

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
        find_resp = self.orkg.predicates.get(q=label, exact=True)
        existing = self._extract_list(find_resp.content)
        if existing:
            return existing[0]["id"]

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
        get_resp = self.orkg.predicates.get(q=label)
        predicates = self._extract_list(get_resp.content)
        if predicates:
            try:
                predicates.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            except Exception:
                pass
            return predicates[0]["id"]
        raise RuntimeError(f"Unable to find or create predicate '{label}'")

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
            get_resp = self.orkg.resources.get(q=label, exact=True)
            items = self._extract_list(get_resp.content)
            if items:
                return items[0]["id"]
        except Exception:
            pass
        # Fallback: get the most recently created resource with this label
        list_resp = self.orkg.resources.get(q=label)
        resources = self._extract_list(list_resp.content)
        if resources:
            try:
                resources.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            except Exception:
                pass
            return resources[0]["id"]
        raise RuntimeError(f"Unable to locate created resource '{label}'")

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
        existing_resp = self.orkg.literals.get_all(q=label, exact=True)
        existing = self._extract_list(existing_resp.content)
        if existing:
            return existing[0]["id"]

        # Note: ORKG literals API doesn't support custom IDs
        resp = self.orkg.literals.add(label=label, datatype=datatype)

        if not resp.succeeded:
            raise RuntimeError(
                f"Literal '{label}' creation failed: {resp.status_code} {resp.content}"
            )

        # The response `.content` for POST returns the created object; try to extract id
        created = resp.content
        try:
            if isinstance(created, dict) and "id" in created:
                return created["id"]
        except Exception:
            pass

        # Fallback to exact lookup if response does not contain ID
        new_resp = self.orkg.literals.get_all(q=label, exact=True)
        new_list = self._extract_list(new_resp.content)
        if new_list:
            return new_list[0]["id"]
        raise RuntimeError(f"Unable to locate created literal '{label}'")

    def add_statement(self, subject_id, predicate_id, object_id):
        """Add a statement to ORKG"""
        return self.orkg.statements.add(
            subject_id=subject_id, predicate_id=predicate_id, object_id=object_id
        )
