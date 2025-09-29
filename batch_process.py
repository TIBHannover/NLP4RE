#!/usr/bin/env python3
"""
Batch Processing Script for PDF to ORKG Instance Creation

This script processes all PDF files in a folder by:
1. Running pdf2JSON.py on each PDF file to extract form data
2. Running create_instance.py on each generated JSON file to create ORKG instances

Usage:
    python batch_process.py <folder_path>
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Tuple
import time


class BatchProcessor:
    """Handles batch processing of PDF files to ORKG instances"""

    def __init__(self, base_dir: str = None):
        """Initialize the batch processor"""
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.pdf2json_script = self.base_dir / "pdf2JSON.py"
        self.create_instance_script = self.base_dir / "create_instance.py"

        # Verify scripts exist
        if not self.pdf2json_script.exists():
            raise FileNotFoundError(f"pdf2JSON.py not found at {self.pdf2json_script}")
        if not self.create_instance_script.exists():
            raise FileNotFoundError(
                f"create_instance.py not found at {self.create_instance_script}"
            )

    def find_pdf_files(self, folder_path: str) -> List[Path]:
        """Find all PDF files in the specified folder"""
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        pdf_files = list(folder.glob("*.pdf"))
        print(f"📁 Found {len(pdf_files)} PDF files in {folder_path}")
        return pdf_files

    def run_pdf2json(self, pdf_path: Path) -> Tuple[bool, Path]:
        """Run pdf2JSON.py on a single PDF file"""
        print(f"\n🔄 Converting PDF to JSON: {pdf_path.name}")

        try:
            # Run pdf2JSON.py with the PDF file path as input
            result = subprocess.run(
                [sys.executable, str(self.pdf2json_script)],
                input=str(pdf_path),
                text=True,
                capture_output=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                # Check if JSON file was created
                json_path = pdf_path.with_suffix(".json")
                if json_path.exists():
                    print(f"  ✅ Successfully created: {json_path.name}")
                    return True, json_path
                else:
                    print(f"  ❌ JSON file not created for {pdf_path.name}")
                    return False, None
            else:
                print(f"  ❌ Error converting {pdf_path.name}:")
                print(f"    stdout: {result.stdout}")
                print(f"    stderr: {result.stderr}")
                return False, None

        except subprocess.TimeoutExpired:
            print(f"  ⏰ Timeout converting {pdf_path.name}")
            return False, None
        except Exception as e:
            print(f"  ❌ Exception converting {pdf_path.name}: {e}")
            return False, None

    def run_create_instance(self, json_path: Path) -> Tuple[bool, str]:
        """Run create_instance.py on a single JSON file"""
        print(f"\n🏗️  Creating ORKG instance from: {json_path.name}")

        try:
            # Run create_instance.py with the JSON file path as input
            result = subprocess.run(
                [sys.executable, str(self.create_instance_script)],
                input=str(json_path),
                text=True,
                capture_output=True,
                timeout=600,  # 10 minute timeout
            )

            if result.returncode == 0:
                # Try to extract instance ID from output
                output_lines = result.stdout.split("\n")
                instance_id = None

                for line in output_lines:
                    if "Instance ID:" in line:
                        instance_id = line.split("Instance ID:")[-1].strip()
                        break
                    elif "Instance URL:" in line:
                        # Extract ID from URL
                        url = line.split("Instance URL:")[-1].strip()
                        instance_id = url.split("/")[-1]
                        break

                if instance_id:
                    print(f"  ✅ Successfully created instance: {instance_id}")
                    return True, instance_id
                else:
                    print(f"  ⚠️  Instance created but ID not found in output")
                    return True, "Unknown"
            else:
                print(f"  ❌ Error creating instance from {json_path.name}:")
                print(f"    stdout: {result.stdout}")
                print(f"    stderr: {result.stderr}")
                return False, None

        except subprocess.TimeoutExpired:
            print(f"  ⏰ Timeout creating instance from {json_path.name}")
            return False, None
        except Exception as e:
            print(f"  ❌ Exception creating instance from {json_path.name}: {e}")
            return False, None

    def process_folder(self, folder_path: str) -> dict:
        """Process all PDF files in a folder"""
        print(f"{'='*80}")
        print(f"🚀 Starting batch processing of folder: {folder_path}")
        print(f"{'='*80}")

        # Find all PDF files
        pdf_files = self.find_pdf_files(folder_path)

        if not pdf_files:
            print("❌ No PDF files found in the specified folder")
            return {"success": False, "processed": 0, "errors": ["No PDF files found"]}

        # Track results
        results = {
            "total_pdfs": len(pdf_files),
            "pdf_conversions": {"success": 0, "failed": 0},
            "instance_creations": {"success": 0, "failed": 0},
            "created_instances": [],
            "errors": [],
        }

        start_time = time.time()

        # Process each PDF file
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"\n{'─'*60}")
            print(f"📄 Processing {i}/{len(pdf_files)}: {pdf_path.name}")
            print(f"{'─'*60}")

            # Step 1: Convert PDF to JSON
            conversion_success, json_path = self.run_pdf2json(pdf_path)

            if conversion_success:
                results["pdf_conversions"]["success"] += 1

                # Step 2: Create ORKG instance from JSON
                instance_success, instance_id = self.run_create_instance(json_path)

                if instance_success:
                    results["instance_creations"]["success"] += 1
                    results["created_instances"].append(
                        {
                            "pdf": pdf_path.name,
                            "json": json_path.name,
                            "instance_id": instance_id,
                        }
                    )
                else:
                    results["instance_creations"]["failed"] += 1
                    results["errors"].append(
                        f"Failed to create instance from {json_path.name}"
                    )
            else:
                results["pdf_conversions"]["failed"] += 1
                results["errors"].append(f"Failed to convert PDF {pdf_path.name}")

        # Calculate total processing time
        end_time = time.time()
        processing_time = end_time - start_time

        # Print summary
        self.print_summary(results, processing_time)

        return results

    def print_summary(self, results: dict, processing_time: float):
        """Print processing summary"""
        print(f"\n{'='*80}")
        print(f"📊 BATCH PROCESSING SUMMARY")
        print(f"{'='*80}")

        print(f"⏱️  Total processing time: {processing_time:.1f} seconds")
        print(f"📄 Total PDF files: {results['total_pdfs']}")

        print(f"\n🔄 PDF to JSON Conversion:")
        print(f"  ✅ Successful: {results['pdf_conversions']['success']}")
        print(f"  ❌ Failed: {results['pdf_conversions']['failed']}")

        print(f"\n🏗️  ORKG Instance Creation:")
        print(f"  ✅ Successful: {results['instance_creations']['success']}")
        print(f"  ❌ Failed: {results['instance_creations']['failed']}")

        if results["created_instances"]:
            print(f"\n🎉 Successfully Created Instances:")
            for instance in results["created_instances"]:
                print(
                    f"  📄 {instance['pdf']} → {instance['json']} → {instance['instance_id']}"
                )

        if results["errors"]:
            print(f"\n⚠️  Errors encountered:")
            for error in results["errors"]:
                print(f"  ❌ {error}")

        success_rate = (
            results["instance_creations"]["success"] / results["total_pdfs"]
        ) * 100
        print(f"\n📈 Overall success rate: {success_rate:.1f}%")


def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python batch_process.py <folder_path>")
        print("Example: python batch_process.py pdf_files/")
        sys.exit(1)

    folder_path = sys.argv[1]

    try:
        processor = BatchProcessor()
        results = processor.process_folder(folder_path)

        # Exit with appropriate code
        if results["instance_creations"]["success"] > 0:
            print(f"\n🎉 Batch processing completed!")
            sys.exit(0)
        else:
            print(f"\n❌ Batch processing failed!")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error during batch processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
