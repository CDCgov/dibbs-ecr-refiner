#!/bin/bash
echo "LocalStack startup script: Creating S3 bucket..."

awslocal s3 mb s3://local-config-bucket

echo "✅ S3 bucket created."
