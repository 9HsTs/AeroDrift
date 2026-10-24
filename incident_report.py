import os
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Preformatted,
)


# =====================================================
# CONFIGURATION
# =====================================================

REPORT_DIR = "reports"


# =====================================================
# PDF INCIDENT REPORT GENERATOR
# =====================================================

def generate_incident_report(
    drift,
    remediation_code="Not provided",
    execution_status=False,
    execution_message="No execution details provided",
    before_state=None,
    after_state=None,
):
    """
    Generate a PDF incident report for AeroDrift.

    execution_status must reflect the actual outcome
    reported by the execution sandbox.
    """

    if not isinstance(drift, dict):
        raise TypeError("drift must be a dictionary")

    os.makedirs(REPORT_DIR, exist_ok=True)

    timestamp = datetime.now()
    incident_id = timestamp.strftime("%Y%m%d_%H%M%S_%f")

    filename = f"incident_{incident_id}.pdf"
    filepath = os.path.join(REPORT_DIR, filename)

    status = "SUCCESS" if execution_status is True else "FAILED"

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "IncidentTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.darkblue,
        spaceAfter=18,
    )

    heading_style = styles["Heading2"]
    body_style = styles["BodyText"]

    code_style = ParagraphStyle(
        "Code",
        fontName="Courier",
        fontSize=8,
        leading=10,
        backColor=colors.whitesmoke,
        borderPadding=6,
    )

    state_style = ParagraphStyle(
        "State",
        fontName="Courier",
        fontSize=8,
        leading=10,
    )

    story = []

    # -------------------------------------------------
    # DOCUMENT HEADER
    # -------------------------------------------------

    story.append(
        Paragraph("AeroDrift - Incident Report", title_style)
    )

    story.append(
        Paragraph(
            f"<b>Incident ID:</b> {escape(incident_id)}",
            body_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>Generated:</b> "
            f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            body_style,
        )
    )

    story.append(Spacer(1, 0.4 * cm))

    # -------------------------------------------------
    # DRIFT DETAILS
    # -------------------------------------------------

    story.append(
        Paragraph("1. Detected Drift", heading_style)
    )

    details = [
        ["Field", "Value"],
        ["Drift type", drift.get("drift_type", "Unknown")],
        [
            "Resource ID",
            drift.get(
                "security_group_id",
                drift.get("resource_id", "Not provided"),
            ),
        ],
        ["Port", drift.get("port", "Not applicable")],
        ["Protocol", drift.get("protocol", "Not provided")],
        ["CIDR", drift.get("cidr", "Not provided")],
        [
            "Description",
            drift.get("description", "No description provided"),
        ],
    ]

    safe_details = [
        [
            Paragraph(escape(str(cell)), body_style)
            for cell in row
        ]
        for row in details
    ]

    details_table = Table(
        safe_details,
        colWidths=[4 * cm, 12 * cm],
        repeatRows=1,
    )

    details_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 7),
        ])
    )

    story.append(details_table)
    story.append(Spacer(1, 0.4 * cm))

    # -------------------------------------------------
    # REMEDIATION DETAILS
    # -------------------------------------------------

    story.append(
        Paragraph("2. Agent Remediation", heading_style)
    )

    story.append(
        Paragraph(
            "<b>Generated remediation code:</b>",
            body_style,
        )
    )

    story.append(Spacer(1, 0.15 * cm))

    code_text = str(remediation_code)

    story.append(
        Preformatted(code_text, code_style)
    )

    story.append(Spacer(1, 0.3 * cm))

    # -------------------------------------------------
    # EXECUTION RESULT
    # -------------------------------------------------

    story.append(
        Paragraph("3. Execution Result", heading_style)
    )

    story.append(
        Paragraph(
            f"<b>Status:</b> {status}",
            body_style,
        )
    )

    story.append(
        Paragraph(
            "<b>Sandbox message:</b> "
            + escape(str(execution_message)),
            body_style,
        )
    )

    story.append(Spacer(1, 0.3 * cm))

    # -------------------------------------------------
    # BEFORE / AFTER STATE
    # -------------------------------------------------

    story.append(
        Paragraph(
            "4. Infrastructure State Comparison",
            heading_style,
        )
    )

    for label, state in [
        ("Before remediation", before_state),
        ("After remediation", after_state),
    ]:
        story.append(
            Paragraph(
                f"<b>{escape(label)}:</b>",
                body_style,
            )
        )

        if state is None:
            text = "State snapshot not supplied."
        else:
            text = str(state)

        story.append(
            Preformatted(text, state_style)
        )

        story.append(Spacer(1, 0.2 * cm))

    # -------------------------------------------------
    # INCIDENT SUMMARY
    # -------------------------------------------------

    story.append(
        Paragraph("5. Incident Summary", heading_style)
    )

    if execution_status is True:
        summary = (
            "The sandbox reported successful execution of the "
            "remediation action. Verify the after-state to confirm "
            "that the intended infrastructure drift was corrected."
        )
    else:
        summary = (
            "The remediation was not confirmed as successful. "
            "Review the sandbox result and infrastructure state "
            "before attempting another remediation."
        )

    story.append(
        Paragraph(escape(summary), body_style)
    )

    # -------------------------------------------------
    # WRITE PDF
    # -------------------------------------------------

    document = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    document.build(story)

    return filepath


# =====================================================
# TEST INCIDENT REPORT GENERATION
# =====================================================

if __name__ == "__main__":

    sample_drift = {
        "drift_type": "open_sg_port",
        "security_group_id": "sg-mock-app",
        "port": 22,
        "protocol": "tcp",
        "cidr": "0.0.0.0/0",
        "description": "SSH port is open to the internet",
    }

    sample_remediation_code = (
        "ec2.revoke_security_group_ingress(\n"
        " GroupId='sg-mock-app',\n"
        " IpPermissions=[...]\n"
        ")"
    )

    print("=" * 55)
    print("AERODRIFT INCIDENT REPORT GENERATOR")
    print("=" * 55)

    try:
        pdf_path = generate_incident_report(
            drift=sample_drift,
            remediation_code=sample_remediation_code,
            execution_status=True,
            execution_message=(
                "Demonstration only: sample success status."
            ),
            before_state={
                "security_group": "sg-mock-app",
                "port_22": "open to 0.0.0.0/0",
            },
            after_state={
                "security_group": "sg-mock-app",
                "port_22": "removed from mock state",
            },
        )

        print("Incident report generated successfully!")
        print("PDF saved at:")
        print(os.path.abspath(pdf_path))

    except Exception as error:
        print("Failed to generate incident report.")
        print("Error:", error)

    print("=" * 55)
