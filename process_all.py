#!/usr/bin/env python3
"""
Process All JSON Files

Simple script to process both JSON files and create template instances.
"""

from create_instance import TemplateInstanceCreator
import os


def main():
    """Process all JSON files in the pdf2JSON_Results directory"""
    creator = TemplateInstanceCreator()

    # Get all JSON files
    json_dir = "pdf2JSON_Results"
    json_files = [f for f in os.listdir(json_dir) if f.endswith(".json")]

    print(f"Found {len(json_files)} JSON files to process:")
    for file in json_files:
        print(f"  - {file}")

    results = []

    # Process each file
    for json_file in json_files:
        file_path = os.path.join(json_dir, json_file)
        print(f"\n{'='*80}")

        instance_id = creator.process_json_file(file_path)

        results.append(
            {
                "file": json_file,
                "instance_id": instance_id,
                "success": instance_id is not None,
            }
        )

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")

    successful = sum(1 for r in results if r["success"])
    print(f"Processed: {len(results)} files")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")

    print(f"\nResults:")
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['file']}")
        if result["success"]:
            print(f"   Instance: {result['instance_id']}")
            print(
                f"   URL: https://incubating.orkg.org/resource/{result['instance_id']}"
            )


if __name__ == "__main__":
    main()
