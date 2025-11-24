"""
Controllers for Reports
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends

from src.app.services.report_service import report_service
from src.app.dependencies.auth import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/reports/frequent-questions/generate")
async def generate_frequent_questions_report(
    days: int = Query(7, ge=1, le=365, description="Number of days to look back for data"),
    include_category_chart: bool = Query(True, description="Include category distribution chart"),
    include_modality_chart: bool = Query(True, description="Include modality distribution chart"),
    include_submodality_chart: bool = Query(True, description="Include submodality distribution chart"),
):
    """
    Generate frequent questions report, save to MinIO and send via email.

    This endpoint:
    1. Queries Prometheus for frequent questions metrics
    2. Generates charts (bar chart, pie chart, optional category/modality/submodality charts)
    3. Creates a professional PDF report
    4. Saves PDF to MinIO storage
    5. Sends PDF via email to administrators
    6. Returns success confirmation

    Args:
        days: Number of days to analyze (1-365)
        include_category_chart: Whether to include category distribution chart
        include_modality_chart: Whether to include modality distribution chart
        include_submodality_chart: Whether to include submodality distribution chart
        current_user: Authenticated user

    Returns:
        dict: Success confirmation message
    """
    try:
        from src.app.services.storage_service import storage_service
        from src.app.services.email_service import email_service
        from datetime import timedelta

        logger.info(f"Starting report generation job for last {days} days")

        # 1. Generate the PDF report
        pdf_bytes = await report_service.generate_frequent_questions_report(
            days=days,
            include_category_chart=include_category_chart,
            include_modality_chart=include_modality_chart,
            include_submodality_chart=include_submodality_chart
        )

        if not pdf_bytes:
            raise HTTPException(
                status_code=404,
                detail="No data available for the report period"
            )

        # 2. Save PDF to MinIO
        report_date = datetime.now().strftime("%Y-%m-%d")
        pdf_filename = f"reporte_preguntas_frecuentes_{report_date}_{days}_dias.pdf"

        minio_path = storage_service.upload_bytes(
            data=pdf_bytes,
            filename=pdf_filename,
            folder="reports",
            content_type="application/pdf"
        )

        logger.info(f"PDF saved to MinIO: {minio_path}")

        # 3. Send email to all users
        period_start = (datetime.now() - timedelta(days=days)).strftime("%d/%m/%Y")
        period_end = datetime.now().strftime("%d/%m/%Y")
        report_period = f"{period_start} - {period_end}"

        # Get all active user emails from database with validation
        from src.app.db.session import get_async_session
        from src.app.models.user import User
        from src.app.config import settings
        from sqlalchemy import select

        user_emails = []
        async for session in get_async_session():
            # Only get emails from active users
            emails = (await session.execute(select(User.email).where(User.is_active == True))).scalars().all()
            emails = [email.strip() for email in emails if email and email.strip()]

            # Email validation logic
            email_original = settings.mailtrap_from_email
            emails_validate = [
                email_original.replace("@gmail.com", "+self@gmail.com")
                if email == email_original
                else email
                for email in emails
            ]

            logger.info(f"Found {len(emails)} total active users with emails in database")
            logger.info(f"Validated emails: {emails_validate}")
            user_emails = emails_validate

        if not user_emails:
            logger.warning("No user emails found in database, skipping email sending")
            emails_sent = 0
        else:
            # Send email to each user individually
            emails_sent = 0
            for user_email in user_emails:
                email_success = await email_service.send_frequent_questions_report(
                    to_email=user_email,
                    pdf_filename=pdf_filename,
                    pdf_content=pdf_bytes,
                    report_period=report_period
                )

                if email_success:
                    emails_sent += 1
                    logger.info(f"Report email sent successfully to user: {user_email}")
                else:
                    logger.warning(f"Failed to send report email to user: {user_email}")

            logger.info(f"Report emails sent to {emails_sent}/{len(user_emails)} users")

        # 4. Return success confirmation
        return {
            "status": "success",
            "message": "Job ejecutado correctamente",
            "details": {
                "report_period_days": days,
                "pdf_filename": pdf_filename,
                "minio_path": minio_path,
                "emails_sent": emails_sent,
                "pdf_size_bytes": len(pdf_bytes)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in report generation job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error ejecutando job de reporte: {str(e)}"
        )


@router.post("/reports/frequent-questions/download")
async def generate_frequent_questions_report_download(
    days: int = Query(7, ge=1, le=365, description="Number of days to look back for data"),
    include_category_chart: bool = Query(True, description="Include category distribution chart"),
    include_modality_chart: bool = Query(True, description="Include modality distribution chart"),
    include_submodality_chart: bool = Query(True, description="Include submodality distribution chart"),
    current_user=Depends(get_current_active_user),
):
    """
    Generate frequent questions report PDF and return signed download URL.

    This endpoint:
    1. Queries Prometheus for frequent questions metrics
    2. Generates charts (bar chart, pie chart, optional category/modality/submodality charts)
    3. Creates a professional PDF report
    4. Saves PDF to MinIO storage
    5. Returns a signed download URL (expires in 1 hour)

    Args:
        days: Number of days to analyze (1-365)
        include_category_chart: Whether to include category distribution chart
        include_modality_chart: Whether to include modality distribution chart
        include_submodality_chart: Whether to include submodality distribution chart
        current_user: Authenticated user

    Returns:
        dict: Download URL and metadata
    """
    try:
        from src.app.services.storage_service import storage_service

        logger.info(f"Generating PDF report download for last {days} days by user {current_user.name}")

        # 1. Generate the PDF report
        pdf_bytes = await report_service.generate_frequent_questions_report(
            days=days,
            include_category_chart=include_category_chart,
            include_modality_chart=include_modality_chart,
            include_submodality_chart=include_submodality_chart
        )

        if not pdf_bytes:
            raise HTTPException(
                status_code=404,
                detail="No data available for the report period"
            )

        # 2. Save PDF to MinIO
        report_date = datetime.now().strftime("%Y-%m-%d")
        pdf_filename = f"reporte_preguntas_frecuentes_{report_date}_{days}_dias.pdf"

        minio_path = storage_service.upload_bytes(
            data=pdf_bytes,
            filename=pdf_filename,
            folder="reports",
            content_type="application/pdf"
        )

        logger.info(f"PDF saved to MinIO: {minio_path}")

        # 3. Generate signed download URL (expires in 1 hour)
        download_url = storage_service.get_file_url(
            object_name=minio_path,
            expires_in_hours=1
        )

        logger.info(f"Generated signed download URL for PDF: {minio_path}")

        # 4. Return download URL and metadata
        return {
            "status": "success",
            "message": "PDF generado correctamente",
            "download_url": download_url,
            "filename": pdf_filename,
            "expires_in_hours": 1,
            "file_size_bytes": len(pdf_bytes),
            "generated_at": datetime.now().isoformat(),
            "report_period_days": days
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF download: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generando PDF para descarga: {str(e)}"
        )