from pathlib import Path

from saxonche import PySaxonProcessor

# define the base directory and file paths
base_dir = Path(__file__).parent
stylesheet_path = base_dir / "schxslt" / "pipeline-for-svrl.xsl"
eicr_schematron_path = base_dir / "eicr" / "CDAR2_IG_PHCASERPT_R2_STU1.1_SCHEMATRON.sch"
rr_schematron_path = base_dir / "rr" / "CDAR2_IG_PHCR_R2_RR_D1_2017DEC_SCHEMATRON.sch"
eicr_output_path = base_dir / "eicr" / "CDAR2_IG_PHCASERPT_R2_STU1.1_SCHEMATRON.xsl"
rr_output_path = base_dir / "rr" / "CDAR2_IG_PHCR_R2_RR_D1_2017DEC_SCHEMATRON.xsl"


def transform_schematron(processor, input_path, output_path, stylesheet_path):
    """
    Transform a schematron file using the provided stylesheet
    """
    xslt_processor = processor.new_xslt30_processor()

    try:
        compiled_stylesheet = xslt_processor.compile_stylesheet(
            stylesheet_file=str(stylesheet_path)
        )
        print(f"Stylesheet compiled successfully for {input_path.name}")
    except Exception as e:
        print(f"Error during stylesheet compilation for {input_path.name}:", str(e))
        return False

    try:
        result = compiled_stylesheet.transform_to_string(source_file=str(input_path))
        if result:
            print(
                f"Transformation successful for {input_path.name}, writing output to file..."
            )
            with open(output_path, "w") as file:
                file.write(result)
            return True
        else:
            print(
                f"No output was generated from the transformation for {input_path.name}"
            )
            return False
    except Exception as e:
        print(f"Error during transformation for {input_path.name}:", str(e))
        return False


# create an instance of the processor
saxon_processor = PySaxonProcessor(license=False)

# use the processor within a context to ensure proper resource management
with saxon_processor as processor:
    # process eicr schematron
    print("\nProcessing eICR Schematron:")
    eicr_success = transform_schematron(
        processor, eicr_schematron_path, eicr_output_path, stylesheet_path
    )

    # process rr schematron
    print("\nProcessing RR Schematron:")
    rr_success = transform_schematron(
        processor, rr_schematron_path, rr_output_path, stylesheet_path
    )

    # final status report
    print("\nTransformation Summary:")
    print(f"eICR Transformation: {'Success' if eicr_success else 'Failed'}")
    print(f"RR Transformation: {'Success' if rr_success else 'Failed'}")
