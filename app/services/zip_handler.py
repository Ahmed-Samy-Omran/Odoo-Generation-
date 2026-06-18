# -*- coding: utf-8 -*-
"""
ZIP Handler - Utility for creating ZIP files from generated modules
"""

import os
import zipfile
import shutil
from pathlib import Path
from typing import Optional


class ZipHandler:
    """Handle ZIP file creation and management"""

    @staticmethod
    def create_module_zip(module_path: str, output_path: Optional[str] = None) -> str:
        """
        Create a ZIP file from an Odoo module directory

        Args:
            module_path: Path to the module directory
            output_path: Optional path for the ZIP file. If not provided,
                        creates it in the parent directory with module name

        Returns:
            Path to the created ZIP file
        """
        if not os.path.isdir(module_path):
            raise ValueError(f"Module path does not exist: {module_path}")

        # Determine output path
        if output_path is None:
            module_name = os.path.basename(module_path)
            parent_dir = os.path.dirname(module_path)
            output_path = os.path.join(parent_dir, f"{module_name}.zip")

        # Create ZIP file
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            ZipHandler._add_directory_to_zip(zipf, module_path)

        return output_path

    @staticmethod
    def _add_directory_to_zip(zipf: zipfile.ZipFile, directory: str, arcname: str = '') -> None:
        """
        Recursively add directory contents to ZIP file

        Args:
            zipf: ZipFile object
            directory: Directory to add
            arcname: Archive name (relative path in ZIP)
        """
        if not arcname:
            arcname = os.path.basename(directory)

        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                # Calculate archive name (relative path in ZIP)
                rel_path = os.path.relpath(file_path, directory)
                archive_path = os.path.join(arcname, rel_path)
                zipf.write(file_path, archive_path)

    @staticmethod
    def cleanup_module_directory(module_path: str) -> None:
        """
        Remove the module directory after ZIP creation

        Args:
            module_path: Path to the module directory to remove
        """
        if os.path.isdir(module_path):
            shutil.rmtree(module_path)

    @staticmethod
    def create_and_cleanup(module_path: str, output_path: Optional[str] = None) -> str:
        """
        Create ZIP file and clean up the original module directory

        Args:
            module_path: Path to the module directory
            output_path: Optional path for the ZIP file

        Returns:
            Path to the created ZIP file
        """
        zip_path = ZipHandler.create_module_zip(module_path, output_path)
        ZipHandler.cleanup_module_directory(module_path)
        return zip_path

    @staticmethod
    def get_zip_info(zip_path: str) -> dict:
        """
        Get information about a ZIP file

        Args:
            zip_path: Path to the ZIP file

        Returns:
            Dictionary containing ZIP file information
        """
        if not os.path.isfile(zip_path):
            raise ValueError(f"ZIP file does not exist: {zip_path}")

        file_size = os.path.getsize(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zipf:
            file_count = len(zipf.namelist())
            compressed_size = sum(info.compress_size for info in zipf.infolist())

        return {
            'path': zip_path,
            'file_size': file_size,
            'file_count': file_count,
            'compressed_size': compressed_size,
            'compression_ratio': (1 - compressed_size / file_size) * 100 if file_size > 0 else 0
        }
