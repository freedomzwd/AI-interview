from fastapi import APIRouter, Depends
from app.utils import utils
from app.api.backoffice.deps import get_current_admin
from app.exceptions.http_exceptions import APIException
from app.schemas.response import ApiResponse
from app.models.admin import Admin

router = APIRouter()


@router.get("/temporary-credentials")
async def get_temporary_credentials(
    current_admin: Admin = Depends(get_current_admin),
):
    """获取S3临时访问凭证"""
    try:
        temporary_credentials = utils.get_temporary_credentials()
        return ApiResponse.success(data=temporary_credentials)
    except Exception as e:
        raise APIException(status_code=500, message=str(e))
