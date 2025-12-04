"""文件工具函数"""
import os
from typing import Optional


def detect_file_type(filename: str) -> str:
    """
    检测文件类型

    Args:
        filename: 文件名

    Returns:
        文件类型字符串
    """
    ext = get_file_extension(filename)

    type_map = {
        'png': 'image',
        'jpg': 'image',
        'jpeg': 'image',
        'gif': 'image',
        'bmp': 'image',
        'pdf': 'pdf',
        'doc': 'word',
        'docx': 'word',
        'ofd': 'ofd',
        'zip': 'archive',
        'rar': 'archive',
    }

    return type_map.get(ext, 'unknown')


def get_file_extension(filename: str) -> str:
    """
    获取文件扩展名（小写，不含点）

    Args:
        filename: 文件名

    Returns:
        文件扩展名
    """
    return os.path.splitext(filename)[1].lower().lstrip('.')


def is_image_file(filename: str) -> bool:
    """
    判断是否为图片文件

    Args:
        filename: 文件名

    Returns:
        是否为图片
    """
    image_extensions = ['png', 'jpg', 'jpeg', 'gif', 'bmp']
    return get_file_extension(filename) in image_extensions


def is_office_file(filename: str) -> bool:
    """
    判断是否为 Office 文档

    Args:
        filename: 文件名

    Returns:
        是否为 Office 文档
    """
    office_extensions = ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']
    return get_file_extension(filename) in office_extensions


def is_archive_file(filename: str) -> bool:
    """
    判断是否为压缩包

    Args:
        filename: 文件名

    Returns:
        是否为压缩包
    """
    archive_extensions = ['zip', 'rar', '7z', 'tar', 'gz']
    return get_file_extension(filename) in archive_extensions


def is_pdf_file(filename: str) -> bool:
    """
    判断是否为 PDF 文件

    Args:
        filename: 文件名

    Returns:
        是否为 PDF
    """
    return get_file_extension(filename) == 'pdf'


def get_safe_filename(filename: str) -> str:
    """
    生成安全的文件名（移除危险字符）

    Args:
        filename: 原始文件名

    Returns:
        安全的文件名
    """
    # 移除路径遍历字符和危险字符
    dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    safe_name = filename
    for char in dangerous_chars:
        safe_name = safe_name.replace(char, '_')

    return safe_name


def ensure_directory_exists(directory: str) -> None:
    """
    确保目录存在，不存在则创建

    Args:
        directory: 目录路径
    """
    os.makedirs(directory, exist_ok=True)
