#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pathlib import Path
from scripts.PDFFormExtractor import PDFFormExtractor



def main():
    try:
        pdf_file_path = input("Please enter the path to an interactive PDF form: ")

        extractor = PDFFormExtractor(pdf_file_path)
        data = extractor.extract_with_labels()

        if not data:
            print(
                "Could not extract any interactive form data. The PDF might be 'flat'."
            )
            return

        json_output = extractor.to_json()

        output_filename = extractor.pdf_path.with_suffix(".json")
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(json_output)

        print(f"\n✅ Successfully extracted data. Output saved to '{output_filename}'")

        # Show summary
        if "total_questions" in data:
            print(f"\n📊 Extraction Summary:")
            print(f"   • Total questions found: {data['total_questions']}")
            print(
                f"   • Questions with selections: {data['extraction_summary']['questions_with_selections']}"
            )
            print(
                f"   • Total form fields processed: {data['extraction_summary']['total_fields_found']}"
            )

        print("\n--- Sample Question Format ---")
        # Show a sample question to demonstrate the format
        if "questions" in data and data["questions"]:
            sample_question = data["questions"][0]
            if sample_question.get("type") == "Text":
                sample_output = {
                    # "question_id": sample_question["question_id"],
                    "question_text": sample_question["question_text"],
                    "type": sample_question["type"],
                    "answer": sample_question.get("answer", ""),
                }
            else:
                all_opts = sample_question.get("all_options", [])
                sample_output = {
                    # "question_id": sample_question["question_id"],
                    "question_text": sample_question["question_text"],
                    "type": sample_question.get("type"),
                    "selected_answers": sample_question.get("selected_answers", []),
                    "all_options": (
                        all_opts[:3] + ["..."] if len(all_opts) > 3 else all_opts
                    ),
                    "total_options": sample_question.get(
                        "total_options", len(all_opts)
                    ),
                }
            print(json.dumps(sample_output, indent=2, ensure_ascii=False))

        print(f"\n💾 Full structured data saved to: {output_filename}")

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
