"""
Controllers for Reports
"""
import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse

from src.app.services.report_service import report_service
from src.app.dependencies.auth import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/reports/frequent-questions/metadata")
async def get_frequent_questions_report_metadata(
    days: int = Query(7, ge=1, le=365, description="Number of days to look back for data"),
    current_user=Depends(get_current_active_user),
):
    """
    Get metadata about the frequent questions report without generating the full PDF.

    This endpoint provides information about:
    - Total number of questions found
    - Total occurrences
    - Number of categories
    - Whether data is available

    Args:
        days: Number of days to analyze (1-365)
        current_user: Authenticated user

    Returns:
        Dictionary with report metadata
    """
    try:
        metadata = await report_service.get_report_metadata(days=days)
        return metadata

    except Exception as e:
        logger.error(f"Error getting report metadata: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving report metadata: {str(e)}"
        )


@router.get("/reports/frequent-questions/pdf")
async def get_frequent_questions_report_pdf(
    days: int = Query(7, ge=1, le=365, description="Number of days to look back for data"),
    include_category_chart: bool = Query(True, description="Include category distribution chart"),
    current_user=Depends(get_current_active_user),
):
    """
    Generate and return a PDF report of frequent questions.

    This endpoint:
    1. Queries Prometheus for frequent questions metrics
    2. Generates charts (bar chart, pie chart, optional category chart)
    3. Creates a professional PDF report
    4. Returns the PDF as a streaming response

    Args:
        days: Number of days to analyze (1-365)
        include_category_chart: Whether to include category distribution chart
        current_user: Authenticated user

    Returns:
        StreamingResponse with PDF content
    """
    try:
        logger.info(f"Generating PDF report for last {days} days by user")

        # Generate the PDF report
        pdf_bytes = await report_service.generate_frequent_questions_report(
            days=days,
            include_category_chart=include_category_chart
        )

        if not pdf_bytes:
            raise HTTPException(
                status_code=404,
                detail="No data available for the report period"
            )

        # Return PDF as streaming response
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=reporte_preguntas_frecuentes_{days}_dias.pdf",
                "Content-Length": str(len(pdf_bytes))
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating PDF report: {str(e)}"
        )