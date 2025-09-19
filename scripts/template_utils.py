"""
Utility functions for working with ORKG templates
"""

from .orkg_connection import ORKGConnection


class TemplateUtils:
    """Utility functions for template operations"""
    
    def __init__(self):
        """Initialize with ORKG connection"""
        self.orkg_conn = ORKGConnection()
    
    def materialize_template(self, template_id):
        """
        Materialize a specific template
        
        Args:
            template_id (str): The ID of the template to materialize
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.orkg_conn.orkg.templates.materialize_template(template_id)
            print(f"✅ Template {template_id} materialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to materialize template {template_id}: {e}")
            return False
    
    def materialize_all_templates(self):
        """
        Materialize all templates in the system
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.orkg_conn.orkg.templates.materialize_templates()
            print("✅ All templates materialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to materialize all templates: {e}")
            return False
    
    def list_available_templates(self):
        """
        List all available templates that can be materialized
        
        Returns:
            list: List of template information
        """
        try:
            # This would depend on ORKG's API for listing templates
            # For now, we'll provide a placeholder
            print("📋 Listing available templates...")
            print("Note: Use the ORKG web interface to view all available templates")
            print("URL: https://incubating.orkg.org/templates")
            return []
        except Exception as e:
            print(f"❌ Failed to list templates: {e}")
            return []
    
    def check_template_materialization_status(self, template_id):
        """
        Check if a template has been materialized
        
        Args:
            template_id (str): The ID of the template to check
            
        Returns:
            bool: True if materialized, False otherwise
        """
        try:
            # Try to access the template function
            template_function = getattr(
                self.orkg_conn.orkg.templates, 
                f"template_{template_id}", 
                None
            )
            if template_function:
                print(f"✅ Template {template_id} is materialized and available")
                return True
            else:
                print(f"❌ Template {template_id} is not materialized")
                return False
        except Exception as e:
            print(f"❌ Error checking template {template_id}: {e}")
            return False
    
    def create_template_instance_example(self, template_id, sample_data=None):
        """
        Create a sample instance of a materialized template
        
        Args:
            template_id (str): The ID of the materialized template
            sample_data (dict, optional): Sample data for the instance
            
        Returns:
            str: The ID of the created instance, or None if failed
        """
        if not self.check_template_materialization_status(template_id):
            print("Template must be materialized before creating instances")
            return None
        
        try:
            template_function = getattr(
                self.orkg_conn.orkg.templates, 
                f"template_{template_id}"
            )
            
            # Use sample data or create default sample
            if sample_data is None:
                sample_data = {
                    "label": f"Sample Instance of Template {template_id}",
                    # Add more default fields as needed
                }
            
            # Create the instance
            instance = template_function(**sample_data)
            
            # Save the instance
            result = instance.save()
            
            if hasattr(result, 'id'):
                instance_id = result.id
            else:
                # Handle different response formats
                instance_id = str(result) if result else "unknown"
            
            print(f"✅ Created template instance with ID: {instance_id}")
            return instance_id
            
        except Exception as e:
            print(f"❌ Failed to create template instance: {e}")
            print("You may need to provide appropriate parameters for this template")
            return None
    
    def get_template_documentation(self, template_id):
        """
        Get documentation for a materialized template
        
        Args:
            template_id (str): The ID of the materialized template
            
        Returns:
            str: Template documentation
        """
        if not self.check_template_materialization_status(template_id):
            return "Template not materialized"
        
        try:
            template_function = getattr(
                self.orkg_conn.orkg.templates, 
                f"template_{template_id}"
            )
            
            doc = template_function.__doc__
            if doc:
                print(f"📖 Template {template_id} Documentation:")
                print(doc)
                return doc
            else:
                print(f"No documentation available for template {template_id}")
                return "No documentation available"
                
        except Exception as e:
            print(f"❌ Error getting documentation for template {template_id}: {e}")
            return "Error retrieving documentation"
