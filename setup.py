# setup.py

from setuptools import setup, find_packages
import os

setup(
    name='fichaje-unificado',
    version='1.0.0', # Define la versión de tu paquete (ej. 1.0.0)
    packages=find_packages(),
    description='Herramienta de fichaje de jornada laboral con Python y PySide6.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='SrMeirins', # Reemplaza con tu nombre
    url='https://github.com/SrMeirins/Fichator', # Reemplaza con la URL de tu repo
    license='MIT',
    install_requires=[
        'PySide6',
        'matplotlib',
    ],
    # -------------------------------------------------------------------
    # ESTE ES EL PUNTO CLAVE: Define el comando que se ejecutará.
    # Cuando el usuario escriba 'fichaje-app' en la terminal,
    # se llamará a la función main() del archivo main.py.
    entry_points={
        'gui_scripts': [
            'fichaje-app = main:main', 
        ],
    },
    # -------------------------------------------------------------------
    # Incluir archivos de datos no-Python (QSS)
    include_package_data=True,
)