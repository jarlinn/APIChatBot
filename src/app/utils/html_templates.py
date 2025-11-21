"""Module for templates used in send emails"""

def get_pending_questions_email_html(questions: list[dict]) -> str:
    """Generate html body for questions pendings alerts"""
    questions_list = ""
    for q in questions[:10]:
        questions_list += f"""
        <li style="margin: 12px 0; padding: 10px; background: #f8f9fa; border-left: 4px solid #3498db; border-radius: 4px;">
            <strong>{q['question_text']}</strong><br>
            <small style="color: #7f8c8d;">
                Hace {q['days_pending']} día{q['days_pending'] != 1 and 's' or ''}
            </small>
        </li>
        """

    total = len(questions)
    more = total > 10

    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; border-radius: 10px;">
        <h2 style="color: #e74c3c;">Tienes {total} pregunta{'' if total == 1 else 's'} por validar</h2>
        
        <p>Hola,</p>
        <p>Hay preguntas esperando tu revisión en la sección de validación.</p>
        
        <p><strong>Estas son algunas de ellas:</strong></p>
        <ul style="list-style: none; padding: 0;">
            {questions_list}
        </ul>
        
        {f"<p><strong>… y {total - 10} más.</strong></p>" if more else ""}
        
        <div style="margin: 30px 0; text-align: center;">
            <p style="background: #3498db; color: white; padding: 12px 32px; border-radius: 6px; font-weight: bold; font-size: 16px; display: inline-block;">
               Ir a Validación → Filtrar por PENDING
            </p>
        </div>
        
        <p style="color: #95a5a6; font-size: 13px;">
            Este es un correo automático • No responder
        </p>
    </div>
    """
