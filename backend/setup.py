from setuptools import setup, find_packages

setup(
    name="hobbes-backend",
    version="0.1.0",
    description="Hobbes App Backend",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.12",
    install_requires=[
        # Core FastAPI dependencies
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.0.0",
        
        # AWS and DynamoDB
        "boto3>=1.29.0",
        "botocore>=1.32.0",
        
        # Authentication and security
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart>=0.0.6",
        
        # Utilities
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
        ]
    }
) 