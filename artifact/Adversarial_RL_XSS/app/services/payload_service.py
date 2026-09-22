from app.exceptions.xss_exception import XSSException

async def generate_content_from_payload(params, request, templates, validator):
    sanitized_els = []
    for param in params:
        valid, sanitized = validator.validate(param)
        if not valid:
            raise XSSException()
        sanitized_els.append(sanitized)
    # Starlette 1.x wants (request, name, context). Paper code used
    # TemplateResponse(name, {"request": request, ...}) on Starlette 0.27.
    try:
        return templates.TemplateResponse(
            request, "basic_response.html", {"payloads": sanitized_els}
        )
    except TypeError:
        return templates.TemplateResponse(
            "basic_response.html",
            {"request": request, "payloads": sanitized_els},
        )
